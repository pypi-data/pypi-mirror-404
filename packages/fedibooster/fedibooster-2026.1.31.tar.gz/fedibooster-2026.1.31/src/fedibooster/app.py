"""High level logic for lemmy2feed."""

import asyncio
import re
import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Annotated
from typing import Final
from typing import Optional

import msgspec.toml
import stamina
import typer
from diskcache import Cache
from httpx import AsyncClient
from loguru import logger as log
from minimal_activitypub import SearchType
from minimal_activitypub import Status
from minimal_activitypub.client_2_server import ActivityPub
from minimal_activitypub.client_2_server import NetworkError
from minimal_activitypub.client_2_server import RatelimitError
from stamina import retry

from fedibooster import __version__
from fedibooster.boostable import Boostable
from fedibooster.config import Configuration
from fedibooster.config import Fediverse
from fedibooster.config import create_default_config
from fedibooster.config import load_external_config_list
from fedibooster.config import load_external_config_regex

stamina.instrumentation.set_on_retry_hooks([])

CACHE_MAX_AGE_DEFAULT_30_DAYS: Final[int] = 30
ENABLE_MINIMAL_ACTIVITYPUB_LOGGING: Final[bool] = False

if ENABLE_MINIMAL_ACTIVITYPUB_LOGGING:
    import logging

    log_fmt = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s(%(lineno)d) - %(message)s"
    lib_log = logging.getLogger("Minimal-ActivityPub")
    lib_log.setLevel(logging.DEBUG)
    cons = logging.StreamHandler()
    cons.setFormatter(logging.Formatter(log_fmt))
    lib_log.addHandler(cons)


@log.catch
async def main(config_path: Path, max_posts: int | None) -> None:
    """Read communities and post to fediverse account."""
    log.info(f"Welcome to fedibooster({__version__})")

    if config_path.exists():
        with config_path.open(mode="rb") as config_file:
            config_content = config_file.read()
            config = msgspec.toml.decode(config_content, type=Configuration)

    else:
        config = await create_default_config()
        log.debug(f"{config=}")
        with config_path.open(mode="wb") as config_file:
            config_file.write(msgspec.toml.encode(config))
        print("Please review your config file, adjust as needed, and run fedibooster again.")
        sys.exit(0)

    log.debug(f"{config=}")

    async with AsyncClient(http2=True, timeout=30) as client:
        search_tags: list[str] = await load_external_config_list(
            file_locations=config.search_tags_list,
            client=client,
        )
        no_reblog_users_list: list[str] = await load_external_config_list(
            file_locations=config.no_reblog_users_list,
            client=client,
        )
        no_reblog_tags_list: list[str] = await load_external_config_list(
            file_locations=config.no_reblog_tags_list,
            client=client,
        )
        no_reblog_users_regex: list[re.Pattern] = await load_external_config_regex(
            file_locations=config.no_reblog_users_regex,
            client=client,
        )
        no_reblog_tags_regex: list[re.Pattern] = await load_external_config_regex(
            file_locations=config.no_reblog_tags_regex,
            client=client,
        )
        log.debug(f"{search_tags=}")
        log.debug(f"{no_reblog_users_list=}")
        log.debug(f"{no_reblog_tags_list=}")
        log.debug(f"{no_reblog_users_regex=}")
        log.debug(f"{no_reblog_tags_regex=}")

        try:
            instance: ActivityPub
            my_username: str
            instance, my_username = await connect(auth=config.fediverse, client=client)
        except NetworkError as error:
            log.info(f"Unable to connect to your Fediverse account with {error=}")
            log.opt(colors=True).info("<red><bold>Can't continue!</bold></red> ... Exiting")
            sys.exit(1)

        with Cache(directory=".") as cache:
            while True:
                # Boost timeline posts
                max_reblogs = min(max_posts, config.max_reblog) if max_posts else config.max_reblog
                try:
                    await boost_statuses_with_hashtags(
                        instance=instance,
                        my_username=my_username,
                        max_boosts=max_reblogs,
                        limit_tags=config.max_tags,
                        no_reblog_tags=no_reblog_tags_list,
                        no_reblog_tags_regex=no_reblog_tags_regex,
                        no_reblog_users=no_reblog_users_list,
                        no_reblog_users_regex=no_reblog_users_regex,
                        client=client,
                        search_instance=config.fediverse.search_instance,
                        tags=search_tags,
                        reblog_sensitive=config.reblog_sensitive,
                        cache=cache,
                    )
                except NetworkError as error:
                    log.warning(f"We've encountered the following error when boosting statuses: {error}")

                if not config.run_continuously:
                    break

                wait_until = datetime.now(tz=UTC) + timedelta(seconds=config.delay_between_posts)
                log.opt(colors=True).info(
                    f"<dim>Waiting until {wait_until:%Y-%m-%d %H:%M:%S %z} "
                    f"({config.delay_between_posts}s) before checking again.</>"
                )
                await asyncio.sleep(delay=config.delay_between_posts)


async def boost_statuses_with_hashtags(  # noqa: PLR0913
    instance: ActivityPub,
    my_username: str,
    max_boosts: int,
    limit_tags: int | None,
    no_reblog_tags: list[str],
    no_reblog_users: list[str],
    no_reblog_tags_regex: list[re.Pattern],
    no_reblog_users_regex: list[re.Pattern],
    client: AsyncClient,
    search_instance: str,
    tags: list[str],
    reblog_sensitive: bool,
    cache: Cache,
) -> None:
    """Boost posts on home timeline."""
    retry_caller = stamina.AsyncRetryingCaller(attempts=3)
    max_id: str = cache.get(key="max-boosted-id")

    search_on: str = search_instance if search_instance else instance.instance

    statuses = await get_statuses_with_tags(search_instance=search_on, tags=tags)

    log.debug(f"Retrieved {len(statuses)} statuses to consider")

    number_boosted: int = 0

    if not statuses:
        return

    for status in reversed(statuses):
        # Check for any reason to skip reblogging this status
        boostable = Boostable(status=status)

        if boostable.has_already_been_boosted(cache=cache):
            continue

        if not boostable.should_be_boosted(
            reblog_sensitive=reblog_sensitive,
            my_username=my_username,
            no_reblog_tags=no_reblog_tags,
            no_reblog_tags_regex=no_reblog_tags_regex,
            no_reblog_users=no_reblog_users,
            no_reblog_users_regex=no_reblog_users_regex,
            search_instance=search_instance,
            limit_tags=limit_tags,
            cache=cache,
        ):
            continue

        # Check Attachments haven't been boosted / rebloged yet
        await boostable.have_attachments_already_been_boosted(cache=cache, client=client)

        # Do the actual reblog
        status_url = boostable.status.get("url", "")
        search_result = await instance.search(query=status_url, query_type=SearchType.STATUSES, resolve=True)
        status_to_reblog = search_result.get("statuses")[0] if search_result.get("statuses") else None
        if status_to_reblog:
            reblog_id = status_to_reblog.get("id")
            await retry_caller(NetworkError, instance.reblog, status_id=reblog_id)
            number_boosted += 1
            log.opt(colors=True).info(f"Boosted <cyan>{status_url}</>")
            boostable.record(cache=cache)

            max_id = reblog_id

        if number_boosted >= max_boosts:
            break

    cache.set(key="max-boosted-id", value=max_id)


async def get_statuses_with_tags(search_instance: str, tags: list[str]) -> list[Status]:
    """Get statuses found on search_instance with tags."""
    statuses: list[Status] = []

    retry_caller = stamina.AsyncRetryingCaller(attempts=3)
    try:
        statuses = await retry_caller(NetworkError, get_hashtag_timeline, search_instance=search_instance, tags=tags)
    except NetworkError as error:
        log.opt(colors=True).info(f"<dim>encountered {error=}</dim>")
    except RatelimitError:
        log.opt(colors=True).info("<dim>We've been rate limited... waiting for 30 minutes</dim>")
        await asyncio.sleep(1800)

    return statuses


def async_shim(
    config_path: Annotated[Path, typer.Argument(help="path to config file")],
    logging_config_path: Annotated[
        Optional[Path], typer.Option("-l", "--logging-config", help="Full Path to logging config file")
    ] = None,
    max_posts: Annotated[
        Optional[int], typer.Option(help="maximum number of posts and reblogs before quitting")
    ] = None,
) -> None:
    """Start async part."""
    if logging_config_path and logging_config_path.is_file():
        with logging_config_path.open(mode="rb") as log_config_file:
            logging_config = msgspec.toml.decode(log_config_file.read())

        for handler in logging_config.get("handlers"):
            if handler.get("sink") == "sys.stdout":
                handler["sink"] = sys.stdout

        log.configure(**logging_config)

    asyncio.run(main(config_path=config_path, max_posts=max_posts))


def typer_shim() -> None:
    """Run actual code."""
    try:
        typer.run(async_shim)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    typer.run(async_shim)


@retry(on=NetworkError, attempts=3)
async def connect(auth: Fediverse, client: AsyncClient) -> tuple[ActivityPub, str]:
    """Connect to fediverse instance server and initialise some values."""
    activity_pub = ActivityPub(
        instance=auth.domain_name,
        access_token=auth.api_token,
        client=client,
    )
    await activity_pub.determine_instance_type()

    user_info = await activity_pub.verify_credentials()

    log.info(f"Successfully authenticated as @{user_info['username']} on {auth.domain_name}")

    return activity_pub, user_info["username"]


@stamina.retry(on=NetworkError, attempts=3)
async def get_hashtag_timeline(search_instance: str, tags: list[str]) -> list[Status]:
    """Search for statuses with 'tags' on 'search_instance'."""
    first_tag = tags[0]
    any_other_tags = tags[1:] if len(tags) > 1 else None
    async with AsyncClient(http2=True, timeout=30) as client:
        search_on = ActivityPub(instance=search_instance, client=client)
        results: list[Status] = await search_on.get_hashtag_timeline(
            hashtag=first_tag,
            any_tags=any_other_tags,
            only_media=True,
            limit=40,
        )

    return results
