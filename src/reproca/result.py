from typing import Literal, Never

import msgspec


class UnwrapError(Exception):
    pass


class Ok[T](msgspec.Struct):
    value: T
    ok: Literal[True] = True

    def unwrap(self) -> T:
        return self.value


class Err[T](msgspec.Struct):
    value: T
    ok: Literal[False] = False

    def unwrap(self) -> Never:
        raise UnwrapError(self.value)


type Result[T, E] = Ok[T] | Err[E]
