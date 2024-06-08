"""Sessions management for reproca applications."""

from __future__ import annotations

__all__ = ["Sessions"]

import secrets
from datetime import UTC, datetime

import msgspec
import pymemcache.client.base
from pymemcache import serde


class Session[T, U](msgspec.Struct):
    userid: T
    user: U
    created: datetime


class Sessions[T, U]:
    def __init__(self, server: tuple[str, int] | str, expire: int = 2592000) -> None:
        """Initialize a sessions manager (Implemented using memcached).

        Args:
        ----
            server: The memcached server address.
            expire: The expiration time of a session in seconds.

        """
        self.client = pymemcache.client.base.Client(server, serde=serde.pickle_serde)
        self.expire = expire

    def create(self, userid: T, user: U) -> str:
        """Create a session for user by user id.

        Usage:
        >>> response.set_session(reproca.sessions.create(...))
        """
        self.remove_by_userid(userid)
        sessionid = secrets.token_urlsafe()
        self.client.set(
            f"sessionid={sessionid}",
            Session(userid, user, datetime.now(tz=UTC)),
            expire=self.expire,
        )
        self.client.set(f"userid={userid}", sessionid)
        return sessionid

    def update_by_sessionid(self, sessionid: str, user: U) -> None:
        """Update a session by session id."""
        session: Session[T, U] | None = self.client.get(f"sessionid={sessionid}")
        if session is None:
            return
        self.client.replace(
            f"sessionid={sessionid}",
            Session(session.userid, user, session.created),
            expire=int(
                self.expire - (datetime.now(tz=UTC) - session.created).total_seconds()
            ),
        )

    def remove_by_userid(self, userid: T) -> None:
        """Remove a session by user id."""
        sessionid: str | None = self.client.get(f"userid={userid}")
        if sessionid is None:
            return
        self.client.delete_many((f"sessionid={sessionid}", f"userid={userid}"))

    def remove_by_sessionid(self, sessionid: str) -> None:
        """Remove a session by session id."""
        session: Session[T, U] | None = self.client.get(f"sessionid={sessionid}")
        if session is None:
            return
        self.client.delete_many((f"sessionid={sessionid}", f"userid={session.userid}"))

    def get_by_userid[D](self, userid: T, default: D = None) -> U | D:
        """Get user by user id, return default if not found."""
        sessionid: str | None = self.client.get(f"userid={userid}")
        if sessionid is None:
            return default
        session: Session[T, U] | None = self.client.get(f"sessionid={sessionid}")
        if session is None:
            return default
        return session.user

    def get_by_sessionid[D](self, sessionid: str, default: D = None) -> U | D:
        """Get user by session id, return default if not found."""
        session: Session[T, U] | None = self.client.get(f"sessionid={sessionid}")
        if session is None:
            return default
        return session.user

    def rate_limit(self, accessor: str, resource: str, rate: int) -> bool:
        """Rate limit an accessor for a resource.

        Returns True if the accessor is NOT allowed to access the resource.

        Args:
        ----
            accessor: The accessor to rate limit.
            resource: The resource to rate limit.
            rate: The rate limit in seconds.

        """
        lock = self.client.get(f"accessor={accessor};resource={resource}")
        if lock:
            return True
        self.client.set(f"accessor={accessor};resource={resource}", True, expire=rate)
        return False
