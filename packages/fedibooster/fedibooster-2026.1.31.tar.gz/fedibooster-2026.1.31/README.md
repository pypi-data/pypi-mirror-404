# Fedibooster

I am taking fedibooster out of 'retirement' for my own **_personal use_**.


[![Repo](https://img.shields.io/badge/repo-Codeberg.org-blue)](https://codeberg.org/MarvinsMastodonTools/fediboster) [![CI](https://ci.codeberg.org/api/badges/13923/status.svg)](https://ci.codeberg.org/repos/13923) [![Downloads](https://pepy.tech/badge/fedibooster)](https://pepy.tech/project/fedibooster)

[![AGPL](https://www.gnu.org/graphics/agplv3-with-text-162x68.png)](https://codeberg.org/MarvinsMastodonTools/fedinesia/src/branch/main/LICENSE.md)

Fedibooster is a command line (CLI) tool / bot / robot to re-blog / boost statuses with hash tags in a given list.
It respects rate limits imposed by servers.

## Install and run from [PyPi](https://pypi.org)

It's ease to install fedibooster from Pypi using the following command

```bash

pip install fedibooster
```

Once installed fedibooster can be started by typing `fedibooster` into the command line.

## Install and run from [Source](https://codeberg.org/marvinsmastodontools/fedibooster)


Alternatively you can run fedibooster from source by cloning the repository using the following command line

```bash

git clone https://codeberg.org/marvinsmastodontools/fedibooster.git
```

fedibooster uses [uv](https://docs.astral.sh/uv/) for dependency control, please install UV before proceeding further.

Before running, make sure you have all required python modules installed. With uv this is as easy as

```bash

uv sync
```

Run fedibooster with the command `uv run fedibooster`

## Configuration / First Run


fedibooster will ask for all necessary parameters when run for the first time and store them in ``config.toml`
file in the current directory.

## License

Fedibooster is licensed under the [GNU Affero General Public License v3.0 ](http://www.gnu.org/licenses/agpl-3.0.html)

## Supporting fedibooster

Fedibooster is a personal project, scratching a personal itch. So by supporting fedibooster you are
in effect supporting me personally. I **don't** provide priority or special support in return for support.

With all that said, there are a number of ways you can support fedibooster:

- You can [buy me a coffee ](https://www.buymeacoffee.com/marvin8).
- You can send me small change in Monero to the address below:

## Monero donation address

`88xtj3hqQEpXrb5KLCigRF1azxDh8r9XvYZPuXwaGaX5fWtgub1gQsn8sZCmEGhReZMww6RRaq5HZ48HjrNqmeccUHcwABg`
