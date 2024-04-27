from secrets import token_urlsafe

from msgspec import Struct, field


class Session(Struct):
    username: str


class Todo(Struct):
    title: str
    description: str
    done: bool
    id: str = field(default_factory=lambda: token_urlsafe(8))
