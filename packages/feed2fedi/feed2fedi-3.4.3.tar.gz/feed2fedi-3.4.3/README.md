# Feed2Fedi

[![Repo](https://img.shields.io/badge/repo-Codeberg.org-blue)](https://codeberg.org/MarvinsMastodonTools/feed2fedi "Repo at Codeberg")
[![CI - Woodpecker](https://ci.codeberg.org/api/badges/MarvinsMastodonTools/feed2fedi/status.svg)](https://ci.codeberg.org/MarvinsMastodonTools/feed2fedi "CI / Woodpecker")
[![Downloads](https://pepy.tech/badge/feed2fedi)](https://pepy.tech/project/feed2fedi "Download count")
[![Checked against](https://img.shields.io/badge/Safety--DB-Checked-green)](https://pyup.io/safety/ "Checked against Safety DB")
[![Checked with](https://img.shields.io/badge/pip--audit-Checked-green)](https://pypi.org/project/pip-audit/ "Checked with pip-audit")
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black "Code style: black")
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/feed2fedi)](https://pypi.org/project/feed2fedi "PyPI – Python Version")
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/feed2fedi)](https://pypi.org/project/feed2fedi "PyPI – Wheel")
[![AGPL](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://codeberg.org/MarvinsMastodonTools/feed2fedi/src/branch/main/license.md "AGPL 3 or later")

Feed2Fedi is a Python bot that reads RSS feeds and automatically posts them to a Fediverse instance.
It supports instances running **Mastodon**, **Takahe**, and **Pleroma**.
Feed2Fedi has been inspired by [feed2toot](https://gitlab.com/chaica/feed2toot).

Features
* Posts to [Fediverse](https://fediverse.party/) instances.
* Attaches a picture if the feed item contains a `media_thumbnail`.
* Monitors multiple RSS/Atom feeds at once.
* Fully open-source—no need to give external services full access to your social-media accounts.

Documentation is available [here](https://marvinsmastodontools.codeberg.page/feed2fedi/).
To delete older posts from your Fediverse account, try [Fedinesia](https://pypi.org/project/fedinesia/).

Disclaimer
The developers of Feed2Fedi hold no liability for what you do with this script or what happens to you by using it.
Abusing this script *can* get you banned from Fediverse instances, so read each site’s usage rules carefully.

Setup and usage
Install with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install feed2fedi
```

Once installed you can start it by issuing the `feed2fedi` command.

During the first run it will prompt for some values and create a `config.ini` file with sensible starting settings.
Then edit the `config.ini` file and add the RSS/ATOM feed in the feeds section and remove the sample feed. Detailed information about config options is available in the [documentation](https://marvinsmastodontools.codeberg.page/feed2fedi/).

## Support Feed2Fedi

A big thank you to the good folk over at [CharCha](https://charcha.cc/) who have allowed me to test Feed2Fedi against their instance that is based on [Rebased](https://gitlab.com/soapbox-pub/rebased) and [Soapbox](https://soapbox.pub/).

There are a number of ways you can support Feed2Fedi:

* Create an issue with problems or ideas you have with/for Feed2Fedi
* You can [buy me a coffee](https://www.buymeacoffee.com/marvin8).
* You can send me small change in Monero to the address below:

Monero donation address:
`84oC6aUX4yyRoEk6pMVVdZYZP4JGJZk4KKJq1p7n9ZqLPK8zH3W1vpFAnSxDQGbwmZAeXrE4w4ct6HqAXdM1K9LfCAxZx4u`

## Changelog

See the [Changelog](https://codeberg.org/MarvinsMastodonTools/feed2fedi/src/branch/main/CHANGELOG.rst) for any changes introduced with each version.

## License

Feed2Fedi is licensed under the [GNU Affero General Public License v3.0](http://www.gnu.org/licenses/agpl-3.0.html)
