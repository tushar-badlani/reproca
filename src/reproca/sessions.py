"""Sessions management for reproca applications."""

from __future__ import annotations

__all__ = ["SESSION_VALID_FOR_DAYS", "Sessions"]

import secrets
from datetime import UTC, datetime

import msgspec

SESSION_VALID_FOR_DAYS = 15


class Session[T, U](msgspec.Struct):
    userid: T
    user: U
    created: datetime

    def is_expired(self) -> bool:
        return (datetime.now(tz=UTC) - self.created).days > SESSION_VALID_FOR_DAYS


class Sessions[T, U]:
    def __init__(self) -> None:
        self.sessions: dict[str, Session[T, U]] = {}
        self.users: dict[T, str] = {}

    def create(self, userid: T, user: U) -> str:
        """Create a session for user by user id.

        Usage:
        >>> response.set_session(reproca.sessions.create(...))
        """
        self.remove_by_userid(userid)
        sessionid = secrets.token_urlsafe()
        self.users[userid] = sessionid
        self.sessions[sessionid] = Session(userid, user, datetime.now(tz=UTC))
        return sessionid

    def remove_by_userid(self, userid: T) -> None:
        """Remove a session by user id."""
        try:
            sessionid = self.users.pop(userid)
            self.sessions.pop(sessionid)
        except KeyError:
            pass

    def remove_by_sessionid(self, sessionid: str) -> None:
        """Remove a session by session id."""
        try:
            session = self.sessions.pop(sessionid)
            self.users.pop(session.userid)
        except KeyError:
            pass

    def get_by_userid[D](self, userid: T, default: D = None) -> U | D:
        """Get user by user id, return default if not found."""
        if sessionid := self.users.get(userid):
            if session := self.sessions.get(sessionid):
                if session.is_expired():
                    self.remove_by_sessionid(sessionid)
                    return default
                return session.user
        return default

    def get_by_sessionid[D](self, sessionid: str, default: D = None) -> U | D:
        """Get user by session id, return default if not found."""
        if session := self.sessions.get(sessionid):
            if session.is_expired():
                self.remove_by_sessionid(sessionid)
                return default
            return session.user
        return default

    def clean_up(self) -> None:
        for sessionid, session in self.sessions.items():
            if session.is_expired():
                self.remove_by_sessionid(sessionid)

    def __len__(self) -> int:
        """Return the number of active sessions."""
        return len(self.sessions)

    def __contains__(self, userid: T) -> bool:
        """Check if a user has an active session."""
        if (sessionid := self.users.get(userid)) and (
            session := self.sessions.get(sessionid)
        ):
            if session.is_expired():
                self.remove_by_userid(userid)
                return False
            return True
        return False
