"""Classes and methods to control configuration of fedibooster."""

import re
from io import StringIO

import msgspec
from httpx import URL
from httpx import AsyncClient
from minimal_activitypub.client_2_server import ActivityPub

from fedibooster import USER_AGENT


class Fediverse(msgspec.Struct):
    """Config values for Fediverse account to cross post to."""

    domain_name: str
    api_token: str
    search_instance: str = ""


class Configuration(msgspec.Struct):
    """Config for bot."""

    fediverse: Fediverse
    run_continuously: bool
    delay_between_posts: int
    search_tags_list: list[str]
    reblog_sensitive: bool = False
    max_reblog: int = 5
    max_tags: int | None = None
    no_reblog_users_list: list[str] | None = None
    no_reblog_users_regex: list[str] | None = None
    no_reblog_tags_list: list[str] | None = None
    no_reblog_tags_regex: list[str] | None = None


async def create_default_config() -> Configuration:
    """Create default configuration."""
    domain_name = input("Please enter the url for your Fediverse instance: ")

    async with AsyncClient(http2=True, timeout=30) as client:
        client_id, client_secret = await ActivityPub.create_app(
            instance_url=domain_name,
            user_agent=USER_AGENT,
            client=client,
        )
        auth_url = await ActivityPub.generate_authorization_url(
            instance_url=domain_name,
            client_id=client_id,
            user_agent=USER_AGENT,
        )

        print("Please go to the following URL and follow the prompts to authorize fedibooster to use your account:")
        print(f"{auth_url}")
        auth_code = input("Please provide the authorization token provided by your instance: ")

        auth_token = await ActivityPub.validate_authorization_code(
            client=client,
            instance_url=domain_name,
            authorization_code=auth_code,
            client_id=client_id,
            client_secret=client_secret,
        )

    return Configuration(
        fediverse=Fediverse(
            domain_name=domain_name,
            api_token=auth_token,
            search_instance="mastodon.social",
        ),
        run_continuously=False,
        delay_between_posts=300,
        max_reblog=5,
        search_tags_list=[
            "https://codeberg.org/marvinsmastodontools/fedibooster-lists/raw/branch/main/tags/search.lst"
        ],
    )


async def load_external_config_regex(file_locations: list[str] | None, client: AsyncClient) -> list[re.Pattern]:
    """Read a text file line-by-line and return a list of compiled
    `re.Pattern` objects, one per non-empty line.
    Blank lines and lines starting with '#' are ignored.
    """
    patterns: list[re.Pattern] = []

    if file_locations:
        for location in file_locations:
            file_location = URL(location)
            source_response = await client.get(url=file_location, follow_redirects=True)
            source_response.raise_for_status()
            content = source_response.text.replace("\r\n", "\n")

            for line in StringIO(content):
                clean_line = line.rstrip("\n")
                if not clean_line or clean_line.startswith("#"):
                    continue
                try:
                    patterns.append(re.compile(clean_line))
                except re.error as exc:
                    raise ValueError(f"Invalid regex on line {line!r}: {exc}") from None

    return patterns


async def load_external_config_list(file_locations: list[str] | None, client: AsyncClient) -> list[str]:
    """Read a text file line-by-line and return a list of compiled
    `re.Pattern` objects, one per non-empty line.
    Blank lines and lines starting with '#' are ignored.
    """
    strings: list[str] = []

    if file_locations:
        for location in file_locations:
            file_location = URL(location)
            source_response = await client.get(url=file_location, follow_redirects=True)
            source_response.raise_for_status()
            content = source_response.text.replace("\r\n", "\n")

            for line in StringIO(content):
                clean_line = line.rstrip("\n")
                if not clean_line or clean_line.startswith("#"):
                    continue
                try:
                    strings.append(clean_line)
                except re.error as exc:
                    raise ValueError(f"Invalid regex on line {line!r}: {exc}") from None

    return strings
