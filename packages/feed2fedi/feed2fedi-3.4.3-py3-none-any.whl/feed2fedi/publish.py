"""Classes and methods needed to publish posts on a Fediverse instance."""

import asyncio
import calendar
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import puremagic
import yt_dlp
import yt_dlp.utils
from feedparser import FeedParserDict
from httpx import AsyncClient
from icecream import ic
from minimal_activitypub.client_2_server import ActivityPub
from minimal_activitypub.client_2_server import ClientError
from minimal_activitypub.client_2_server import NetworkError
from minimal_activitypub.client_2_server import RatelimitError
from stamina import retry
from whenever import Instant
from whenever import TimeDelta
from whenever import ZonedDateTime

from feed2fedi.collect import FeedReader
from feed2fedi.collect import get_file
from feed2fedi.control import Actions
from feed2fedi.control import Configuration
from feed2fedi.control import FeedInfo
from feed2fedi.control import IgnoringLogger
from feed2fedi.control import PostRecorder


class Fediverse:
    """Helper class to publish posts on a fediverse instance from rss feed items."""

    def __init__(self, config: Configuration, post_recorder: PostRecorder) -> None:
        self.config = config
        self.post_recorder = post_recorder
        self.max_age: TimeDelta | None = None

    async def publish(
        self,
        items: list[FeedParserDict],
        feed: FeedInfo,
        post_limit: int | None,
        delay: TimeDelta | None,
        client: AsyncClient,
    ) -> int:
        """Publish posts to fediverse instance from content in the items list.

        :param post_limit: Optional; Number of statuses to post before returning
        :param items: Rss feed items to post
        :param feed: Section of config for current feed
        :param scheduled_at: datetime for when the statuses should be scheduled.
            None for immediate posting.
        :param client: httpx AsyncClient to use for posting to fedi instance.

        :returns int: Number of new statuses posted.
        """
        post_template = self._determine_post_template(feed_template=feed.post_template)
        fediverse = await self._connect_fediverse(client=client)

        max_size = fediverse.max_att_size

        if isinstance(feed.max_attachments, int):
            max_media = min(fediverse.max_attachments, feed.max_attachments)
        else:
            max_media = fediverse.max_attachments

        if feed.max_age:
            self.max_age = TimeDelta.parse_iso(feed.max_age)

        statuses_posted = 0

        for item in items:
            skip, sensitive, spoiler_text = await self._pre_publish_checks(item=item, feed=feed)
            if skip:
                continue

            try:
                status = Fediverse._determine_status(feed=feed, item=item, post_template=post_template)

                media_ids = await self._post_media(
                    fediverse=fediverse,
                    feed=feed,
                    item=item,
                    max_media=max_media,
                    max_size=max_size,
                )
                ic(media_ids)

                posted_status = await self._post_actual_status(
                    fediverse=fediverse,
                    media_ids=media_ids,
                    sensitive=sensitive,
                    spoiler_text=spoiler_text,
                    status=status,
                    delay=delay,
                )
                ic()

                log_posted_status(posted_status=posted_status)

                await self.post_recorder.log_post(shared_url=item.link)

                statuses_posted += 1
                if post_limit and statuses_posted >= post_limit:
                    break
                elif feed.max_posts and statuses_posted >= feed.max_posts:
                    break

            except RatelimitError:
                reset = fediverse.ratelimit_reset
                seconds = reset.timestamp() - ZonedDateTime.now("UTC").timestamp()
                print(
                    f'!!! Server "cool down" - waiting until {reset:%Y-%m-%d %H:%M:%S %z} '
                    f"({round(number=seconds)} seconds)"
                )
                await asyncio.sleep(delay=seconds)

            except (ClientError, KeyError) as error:
                print(f"!!! Encountered error: {error}\nLog article to avoid repeat of error")
                await self.post_recorder.log_post(shared_url=item.link)
                continue

        return statuses_posted

    @staticmethod
    def _determine_status(feed: FeedInfo, item: FeedParserDict, post_template: str) -> str:
        """Build status from all info needed."""
        ic(feed.prefix)
        if feed.prefix:
            prefix = f"{feed.prefix} - "
        else:
            prefix = ""

        ic(item["params"])
        status = prefix + post_template.format(**item["params"]).replace("\\n", "\n")
        return status

    async def _pre_publish_checks(self, item: FeedParserDict, feed: FeedInfo) -> tuple[bool, bool, str | None]:
        """Check item before posting status."""
        skip = False
        sensitive = False
        spoiler_text: str | None = None

        if await self.post_recorder.duplicate_check(identifier=item.link):
            skip = True

        elif self._item_too_old(item=item):
            await self.post_recorder.log_post(shared_url=item.link)
            skip = True

        if not skip:
            skip, sensitive, spoiler_text = await self._apply_filters(feed, item)
            if skip:
                await self.post_recorder.log_post(shared_url=item.link)

        return skip, sensitive, spoiler_text

    @retry(on=NetworkError, attempts=3)
    async def _post_actual_status(  # noqa: PLR0913
        self,
        fediverse: ActivityPub,
        media_ids: list[str] | None,
        sensitive: bool,
        spoiler_text: str | None,
        delay: TimeDelta | None,
        status: str,
    ):
        """Post actual status. This has been refactored into its own method to be able to apply retry logic."""
        scheduled_at: datetime | None = None
        if delay:
            scheduled_at = (ZonedDateTime.now_in_system_tz() + delay).py_datetime()

        ic(status)
        ic(self.config.bot_post_visibility)
        ic(media_ids)
        ic(sensitive)
        ic(spoiler_text)
        ic(scheduled_at)
        posted_status = await fediverse.post_status(
            status=status,
            visibility=self.config.bot_post_visibility,
            media_ids=media_ids,
            sensitive=sensitive,
            spoiler_text=spoiler_text,
            scheduled_at=scheduled_at,
        )
        ic()
        return posted_status

    async def _post_media(
        self,
        fediverse: ActivityPub,
        feed: FeedInfo,
        item: FeedParserDict,
        max_media: int,
        max_size: int,
    ) -> list[str] | None:
        """Post media if configured to do so."""
        media_ids: list[str] | None = None
        if self.config.bot_post_media and max_media:
            media_ids = await Fediverse._post_video(
                fediverse=fediverse,
                item=item,
                post_videos=feed.post_videos,
                max_size=max_size,
            )

            if not media_ids:
                media_ids = await Fediverse._post_images(
                    fediverse=fediverse,
                    item=item,
                    max_images=max_media,
                    image_selector=self.config.bot_post_image_selector,
                    supported_mime_types=fediverse.supported_mime_types,
                    max_size=max_size,
                )
        return media_ids

    def _item_too_old(self, item: FeedParserDict) -> bool:
        """Check if item is older than max_age."""
        if not self.max_age:
            return False

        ic(item.get("published_parsed"))
        ic(item.get("updated_parsed"))
        date_for_age = item.get("published_parsed")
        if date_for_age is None:
            date_for_age = item.get("updated_parsed")

        if date_for_age is None:
            # Neither published nor updated date has been supplied.
            # Since we are here we want to age check feed items and
            # since we don't have the information to determine the age
            # we return True to say it is likely too old and the
            # feed item should get skipped.
            return True

        timestamp = calendar.timegm(date_for_age)
        temp_inst = Instant.from_timestamp(timestamp)
        age_of_article = Instant.now() - temp_inst
        ic(age_of_article)
        ic(self.max_age)
        if self.max_age and age_of_article > self.max_age:
            ic()
            return True

        return False

    @staticmethod
    async def _apply_filters(feed, item) -> tuple[bool, bool, str | None]:
        """Apply filters to item."""
        filter_action_drop = False
        sensitive = False
        spoiler_text = None
        for item_filter in feed.filters:
            if item_filter.do_check(item):
                if item_filter.action == Actions.DROP:
                    filter_action_drop = True
                    break
                elif item_filter.action == Actions.SEARCH_REPLACE:
                    search = item_filter.action_params["search"]
                    replace = item_filter.action_params["replace"]
                    item["params"]["content_html"] = re.sub(search, replace, item["params"]["content_html"])
                    item["params"]["content_markdown"] = re.sub(search, replace, item["params"]["content_markdown"])
                    item["params"]["content_plaintext"] = re.sub(search, replace, item["params"]["content_plaintext"])
                elif item_filter.action == Actions.MARK_CW:
                    sensitive = True
                    spoiler_text = item_filter.action_params
        return filter_action_drop, sensitive, spoiler_text

    @staticmethod
    @retry(on=NetworkError, attempts=3)
    async def _post_video(
        fediverse: ActivityPub,
        item: FeedParserDict,
        post_videos: bool,
        max_size: int,
    ) -> list[str]:
        """Post media to fediverse instance and return media ID.

        :param fediverse: ActivityPub api instance
        :param item: Feed item to load media from
        :param post_videos: Boolean indicating whether videos should be posted.
        :returns:
            List containing no, one  or multiple strings of the media id after upload
        """
        media_ids: list[str] = []
        filenames: list[str] = []

        if not post_videos:
            return media_ids

        ic()
        try:
            filenames = await Fediverse._get_video(item)
        except yt_dlp.utils.DownloadError:
            # Skip and go to next processing type
            pass
        ic(filenames)

        if len(filenames) > 0:
            for filename in filenames:
                magic_info = puremagic.magic_file(filename=filename)
                mime_type = magic_info[0].mime_type
                ic(Path(filename).stat())
                ic(max_size)
                if Path(filename).stat().st_size > max_size:
                    continue  # Skip files that are too large
                try:
                    if mime_type:
                        with Path(filename).open(mode="rb") as file:
                            media = await fediverse.post_media(file=file, mime_type=mime_type)
                        media_ids.append(media.get("id"))
                except ClientError as error:
                    raise ClientError from error
                finally:
                    Path(filename).unlink()

        return media_ids

    @staticmethod
    async def _get_video(item) -> list[str]:
        """Download videos."""
        ic()
        filenames: list[str] = []
        ydl_opts = {
            "quiet": "true",
            "logger": IgnoringLogger(),
            "no_warnings": "true",
            "ignoreerrors": "true",
            "outtmpl": "%(id)s.%(ext)s",
        }
        ic(item.link)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.link, download=True)
            ydl_info = ydl.sanitize_info(info)
            ic(ydl_info)
            if ydl_info and ydl_info.get("requested_downloads"):
                ic(ydl_info.get("requested_downloads"))
                for dl in ydl_info.get("requested_downloads"):
                    ic(dl.get("filepath"))
                    if filename := dl.get("filepath"):
                        filenames.append(filename)
        return filenames

    @retry(on=NetworkError, attempts=3)
    async def _connect_fediverse(self, client: AsyncClient) -> ActivityPub:
        fediverse = ActivityPub(
            instance=self.config.fedi_instance,
            client=client,
            access_token=self.config.fedi_access_token,
        )
        await fediverse.determine_instance_type()
        await fediverse.verify_credentials()

        return fediverse

    @staticmethod
    @retry(on=NetworkError, attempts=3)
    async def _post_images(  # noqa: PLR0913
        fediverse: ActivityPub,
        item: FeedParserDict,
        image_selector: str,
        supported_mime_types: list[str],
        max_images: int,
        max_size: int,
    ) -> list[str]:
        """Post media to fediverse instance and return media ID.

        :param fediverse: ActivityPub api instance
        :param item: Feed item to load media from
        :param max_images: number of images to post. Defaults to 1
        :param supported_mime_types:  List of strings representing mime types supported by the instance server

        :returns:
            List containing no, one  or multiple strings of the media id after upload
        """
        ic(max_images)
        ic(max_size)
        media_ids: list[str] = []
        media_urls = FeedReader.determine_image_url(item, image_selector)

        for url in media_urls:
            if len(media_ids) == max_images:
                break

            ic(url)
            with tempfile.TemporaryFile() as temp_image_file:
                mime_type = await get_file(img_url=url, file=temp_image_file, supported_mime_types=supported_mime_types)
                temp_image_file.seek(0, 2)
                file_size = temp_image_file.tell()
                ic(file_size)
                ic(mime_type)
                if mime_type and file_size <= max_size:
                    temp_image_file.seek(0)
                    media = await fediverse.post_media(
                        file=temp_image_file,
                        mime_type=mime_type,
                    )
                    ic(media)
                    media_ids.append(media["id"])

        return media_ids

    def _determine_post_template(self, feed_template: str | None) -> str:
        """Determine with post template to use."""
        post_template = self.config.bot_post_template
        if feed_template:
            post_template = feed_template

        return post_template


def log_posted_status(posted_status: dict[str, Any]) -> None:
    """Log what has been posted to the console."""
    ic(posted_status.get("url"))
    if "content" in posted_status:
        print(f"Posted {posted_status['content']} to Fediverse at\n{posted_status['url']}")
    else:
        print(
            f"Scheduled {posted_status['params']['text']} to Fediverse for posting at \n{posted_status['scheduled_at']}"
        )
