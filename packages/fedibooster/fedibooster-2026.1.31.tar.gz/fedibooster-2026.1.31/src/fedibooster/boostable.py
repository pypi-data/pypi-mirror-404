"""Logic all around a boostable status."""

import re
from dataclasses import dataclass
from dataclasses import field
from hashlib import sha256
from typing import Final
from urllib.parse import urlparse

from diskcache import Cache
from httpx import AsyncClient
from loguru import logger as log
from minimal_activitypub import Status

CACHE_MAX_AGE_DEFAULT_30_DAYS: Final[int] = 30


@dataclass
class Boostable:
    """Represents a status that can be boosted."""

    status: Status
    attachments_hashes: list[str] = field(default_factory=list)

    def bot_status(self) -> bool:
        """Check if status has been made by a bot account."""
        if self.status.get("account", {}).get("bot"):
            log.opt(colors=True).debug(
                f"<dim><red>Not Boosting</red> <cyan>{self.status.get('url', '')}</cyan> "
                f"because it was posted by a bot</dim>"
            )
            return True

        return False

    def sensitive_status_blocked(self, reblog_sensitive: bool) -> bool:
        """Check if the status is marked as sensitive and if check if we allow rebloging sensitve statuses."""
        status_sensitive: bool = self.status.get("sensitive", False)
        if status_sensitive and not reblog_sensitive:
            log.opt(colors=True).debug(
                f"<dim><red>Not Boosting</red> sensitive status - <cyan>{self.status.get('url', '')}</cyan></dim>"
            )
            return True

        return False

    def my_own_status(self, my_username: str) -> bool:
        """Check if the status was posted by myself."""
        if self.status.get("account", {}).get("username") == my_username:
            log.opt(colors=True).debug(
                f"<dim><red>Skipping</red> post from myself - <cyan>{self.status.get('url', '')}</cyan></dim>"
            )
            return True

        return False

    def no_attachments(self) -> bool:
        """Check if the status as NO attachments."""
        if not len(self.status.get("media_attachments", [])):
            log.opt(colors=True).debug(
                f"<dim><red>Not Boosting</red> <cyan>{self.status.get('url', '')}</cyan> "
                f"because it has no attachments / media</dim>"
            )
            return True

        return False

    def too_many_tags(self, limit: int | None) -> bool:
        """Determine if status has more than `limit` tags."""
        if limit and len(self.status.get("tags", [])) > limit:
            log.opt(colors=True).debug(
                f"<dim><red>Not Boosting</red> <cyan>{self.status.get('url', '')}</cyan> "
                f"because it has more than <red>{limit}</red> tags.</dim>"
            )
            return True

        return False

    def by_no_reblog_user(self, no_reblog_users: list[str], search_host: str) -> bool:
        """Check if status was posted by a user in the no_reblog_users list."""
        username = self.status.get("account", {}).get("acct")
        if "@" not in username:
            username = self.expand_local_user(username=username, search_host=search_host)
        log.debug(f"{username=}")

        for no_reblog_user in no_reblog_users:
            if re.search(rf"{no_reblog_user}", username):
                log.opt(colors=True).debug(
                    f"<dim><red>Not Boosting</red> <cyan>{self.status.get('url', '')}</cyan> "
                    f"because it was posted by a '{username}' who is a match in for {no_reblog_user} "
                    f"in the no_reblog_users list</dim>"
                )
                return True

        return False

    def by_no_reblog_regex(self, no_reblog_regexs: list[re.Pattern], search_host: str) -> bool:
        """Check if status was posted by a user in the no_reblog_users list."""
        username = self.status.get("account", {}).get("acct")
        if "@" not in username:
            username = self.expand_local_user(username=username, search_host=search_host)
        log.debug(f"{username=}")

        return next((p for p in no_reblog_regexs if p.search(username)), None) is not None

    @staticmethod
    def expand_local_user(username: str, search_host: str) -> str:
        """Expand username that don't contain a hostname."""
        hostname = search_host
        parsed = urlparse(url=search_host)
        if parsed.hostname:
            hostname = parsed.hostname
        expanded_username = f"{username}@{hostname}"
        log.debug(f"Expanded {username} to {expanded_username}")

        return expanded_username

    def has_no_reblog_tag(self, no_reblog_tags: list[str]) -> bool:
        """Check if status contains any tag in the no_reblog_tags list."""
        status_tags: list[str] = [x["name"].casefold() for x in self.status.get("tags", [])]
        log.debug(f"{status_tags=}")
        if any(no_reblog.casefold() in status_tags for no_reblog in no_reblog_tags):
            log.opt(colors=True).debug(
                f"<dim><red>Not Boosting</red> <cyan>{self.status.get('url', '')}</cyan> "
                f"because it contains tags that are in the no_reblog_tags list</dim>"
            )
            return True

        return False

    def has_no_reblog_regex(self, no_reblog_regexs: list[re.Pattern]) -> bool:
        """Check if contains any tag that matches any regex."""
        status_tags: list[str] = [x["name"].casefold() for x in self.status.get("tags", [])]
        log.debug(f"{status_tags=}")

        return any(pattern.search(tag) for tag in status_tags for pattern in no_reblog_regexs)

    def record(self, cache: Cache) -> None:
        """Record a status having been rebloged."""
        status_id = self.status.get("id")
        status_url = self.status.get("url")
        status_apid = self.status.get("ap_id")
        cache.set(status_id, True, expire=CACHE_MAX_AGE_DEFAULT_30_DAYS * 86400)
        if status_url:
            cache.set(key=status_url, value=True, expire=CACHE_MAX_AGE_DEFAULT_30_DAYS * 86400)
        if status_apid:
            cache.set(key=status_apid, value=True, expire=CACHE_MAX_AGE_DEFAULT_30_DAYS * 86400)
        if self.attachments_hashes:
            for hash in self.attachments_hashes:
                cache.set(key=hash, value=True, expire=CACHE_MAX_AGE_DEFAULT_30_DAYS * 86400)

    def has_already_been_boosted(self, cache: Cache) -> bool:
        """Perform a number of checks to see if status has already been boosted."""
        status_id = self.status.get("id")
        status_url = self.status.get("url")
        status_apid = self.status.get("ap_id")

        if cache.get(key=status_id, default=False):
            log.debug(f"Status {status_id} has already been boosted. SKIPPING")
            return True

        if status_url and cache.get(key=status_url, default=False):
            log.debug(f"Status URL {status_url} has already been boosted. SKIPPING")
            self.record(cache=cache)
            return True

        if status_apid and cache.get(key=status_apid, default=False):
            log.debug(f"Status ap_id {status_apid} has already been boosted. SKIPPING")
            self.record(cache=cache)
            return True

        return False

    async def have_attachments_already_been_boosted(self, cache: Cache, client: AsyncClient) -> None:
        """Check if at least one attachment has already been boosted.

        If all attachments have not been boosted, return a list of attachment hashes
        otherwise return empty list
        """
        for attachment in self.status.get("media_attachments", []):
            attachment_hash = await determine_attachment_hash(url=attachment.get("url"), client=client)
            if cache.get(key=attachment_hash):
                log.opt(colors=True).info(
                    f"<dim><red>Not Boosting:</red> At least one attachment of status at "
                    f"<cyan>{self.status.get('url')}</cyan> has already been boosted or posted.</dim>"
                )
                self.attachments_hashes = []
                self.record(cache=cache)

            self.attachments_hashes.append(attachment_hash)

    def should_be_boosted(  # noqa: PLR0913
        self,
        reblog_sensitive: bool,
        my_username: str,
        no_reblog_tags: list[str],
        no_reblog_tags_regex: list[re.Pattern],
        no_reblog_users: list[str],
        no_reblog_users_regex: list[re.Pattern],
        search_instance: str,
        limit_tags: int | None,
        cache: Cache,
    ) -> bool:
        """Determine if this should be boosted."""
        if (
            self.bot_status()
            or self.sensitive_status_blocked(reblog_sensitive=reblog_sensitive)
            or self.my_own_status(my_username=my_username)
            or self.no_attachments()
            or self.has_no_reblog_tag(no_reblog_tags=no_reblog_tags)
            or self.has_no_reblog_regex(no_reblog_regexs=no_reblog_tags_regex)
            or self.by_no_reblog_user(no_reblog_users=no_reblog_users, search_host=search_instance)
            or self.by_no_reblog_regex(no_reblog_regexs=no_reblog_users_regex, search_host=search_instance)
            or self.too_many_tags(limit=limit_tags)
        ):
            self.record(cache=cache)
            return False

        return True


async def determine_attachment_hash(url: str, client: AsyncClient) -> str:
    """Determine attachment hash."""
    response = await client.get(url=url)
    url_hash = sha256(response.content).hexdigest()
    return url_hash
