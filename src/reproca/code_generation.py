from enum import Enum
from platform import python_version_tuple

__all__ = ["CodeGenerator"]

import functools
import sys
import typing
from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
)
from datetime import datetime
from types import NoneType, UnionType, get_original_bases
from typing import (
    IO,
    Any,
    Generic,
    Literal,
    TypeAliasType,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import msgspec

from .method import SPECIAL_PARAMETERS, Method


def get_type_alias_value(obj: TypeAliasType) -> object:
    if python_version_tuple() >= ("3", "12"):
        return obj.__value__
    globalns = getattr(sys.modules.get(obj.__module__, None), "__dict__", {})  # type: ignore
    localns = dict(vars(obj))
    return typing._eval_type(obj.__value__, globalns, localns)  # type: ignore


class Writer:
    def __init__(self, file: IO[str]) -> None:
        self.file = file

    def write(self, *strings: str) -> None:
        self.file.writelines(strings)

    def intersperse(
        self, separator: Callable[[], None], funcs: Iterable[Callable[[], None]]
    ) -> None:
        it = iter(funcs)
        func = next(it, None)
        while func is not None:
            func()
            func = next(it, None)
            if func is not None:
                separator()


class CodeGenerator(Writer):
    def __init__(self, file: IO[str]) -> None:
        super().__init__(file)
        self.unresolved: set[type[Enum | msgspec.Struct] | TypeAliasType] = set()
        self.resolved: set[object] = set()

    def resolve(self) -> None:
        if len(self.unresolved) == 0:
            return
        self.resolved.update(self.unresolved)
        unresolved = self.unresolved
        self.unresolved = set()
        for obj in unresolved:
            if isinstance(obj, TypeAliasType):
                self.type_alias(obj)
            elif issubclass(obj, Enum):
                self.enum(obj)
            else:
                self.msgspec_struct(obj)
        self.resolve()

    def enum(self, obj: type[Enum]) -> None:
        self.doc(obj.__doc__)
        self.write("export enum ", obj.__name__, "{")
        for member in obj:
            self.write(member.name, "=")
            self.literal(member.value)
            self.write(",")
        self.write("}")

    def type_alias(self, obj: TypeAliasType) -> None:
        self.write("export type ", obj.__name__)
        if obj.__type_params__:
            self.write("<")
            self.intersperse(
                lambda: self.write(","),
                (
                    functools.partial(self.type_object, param)
                    for param in obj.__type_params__
                ),
            )
            self.write(">")
        self.write("=")
        self.type_object(get_type_alias_value(obj))
        self.write(";")

    def literal(self, obj: object) -> None:
        match obj:
            case None:
                self.write("null")
            case True:
                self.write("true")
            case False:
                self.write("false")
            case int() | float() | str():
                self.write(repr(obj))
            case _:
                msg = f"Unsupported literal type: {obj!r}"
                raise TypeError(msg)

    def type_object(self, type_object: object) -> None:
        match type_object:
            case type() if issubclass(type_object, Enum):
                if type_object not in self.resolved:
                    self.unresolved.add(type_object)
                self.write(type_object.__name__)
            case msgspec.UnsetType():
                self.write("undefined")
            case type() if issubclass(type_object, NoneType):
                self.write("null")
            case None:
                self.write("null")
            case type() if issubclass(type_object, bool):
                self.write("boolean")
            case type() if issubclass(type_object, int | float):
                self.write("number")
            case type() if issubclass(type_object, str | bytes | bytearray | datetime):
                self.write("string")
            case type() if issubclass(type_object, msgspec.Struct):
                if type_object not in self.resolved:
                    self.unresolved.add(type_object)
                self.write(type_object.__name__)
            case type() if type_object is msgspec.UnsetType:
                self.write("undefined")
            case TypeVar():
                self.write(type_object.__name__)
            case TypeAliasType():
                if type_object not in self.resolved:
                    self.unresolved.add(type_object)
                self.write(type_object.__name__)
            case type() if type_object is Any:
                self.write("any")
            case _:
                self.generic_type(type_object)

    def generic_type(self, type_object: object) -> None:
        orig = get_origin(type_object)
        match orig:
            case TypeAliasType():
                args = get_args(type_object)
                if orig not in self.resolved:
                    self.unresolved.add(orig)
                self.write(orig.__name__)
                self.write("<")
                self.intersperse(
                    lambda: self.write(","),
                    (functools.partial(self.type_object, arg) for arg in args),
                )
                self.write(">")
            case type() if issubclass(orig, msgspec.Struct):
                args = get_args(type_object)
                if orig not in self.resolved:
                    self.unresolved.add(orig)
                self.write(orig.__name__)
                self.write("<")
                self.intersperse(
                    lambda: self.write(","),
                    (functools.partial(self.type_object, arg) for arg in args),
                )
                self.write(">")
            case type() if issubclass(orig, tuple):
                args = get_args(type_object)
                if args[1:] == (...,):
                    self.type_object(list[args[0]])  # type: ignore
                    return
                self.write("[")
                self.intersperse(
                    lambda: self.write(","),
                    (functools.partial(self.type_object, arg) for arg in args),
                )
                self.write("]")
            case type() if issubclass(orig, dict | Mapping | MutableMapping):
                args = get_args(type_object)
                self.write("Record<")
                self.type_object(args[0])
                self.write(", ")
                self.type_object(args[1])
                self.write(">")
            case type() if issubclass(
                orig,
                list
                | set
                | frozenset
                | Collection
                | Sequence
                | MutableSequence
                | MutableSet,
            ):
                self.write("(")
                self.type_object(get_args(type_object)[0])
                self.write(")[]")
            case orig if orig is Literal:
                self.intersperse(
                    lambda: self.write("|"),
                    (
                        functools.partial(self.literal, arg)
                        for arg in get_args(type_object)
                    ),
                )
            case _ if orig is UnionType or orig is Union:

                def do(arg: object) -> None:
                    self.write("(")
                    self.type_object(arg)
                    self.write(")")

                self.write("(")
                self.intersperse(
                    lambda: self.write("|"),
                    (functools.partial(do, arg) for arg in get_args(type_object)),
                )
                self.write(")")
            case _:
                msg = f"Could not convert type: {type_object!r}, origin: {orig!r}"
                raise TypeError(msg)

    def doc(self, doc: str | None) -> None:
        if doc:
            self.write(f"/** {doc} */\n")

    def msgspec_struct(self, struct: type[msgspec.Struct]) -> None:
        self.doc(struct.__doc__)
        self.write("export interface ", struct.__name__)
        if params := next(
            (
                get_args(base)
                for base in get_original_bases(struct)
                if get_origin(base) is Generic
            ),
            None,
        ):
            self.write("<")
            self.intersperse(
                lambda: self.write(","),
                (functools.partial(self.type_object, param) for param in params),
            )
            self.write(">")
        self.write("{")
        for fieldname, fieldtype in get_type_hints(struct).items():
            optional = False
            if (
                get_origin(fieldtype) is UnionType or get_origin(fieldtype) is Union
            ) and msgspec.UnsetType in (args := get_args(fieldtype)):
                args = (arg for arg in args if arg is not msgspec.UnsetType)
                fieldtype = Union[*args]  # type: ignore
                optional = True
            self.write(fieldname, "?:" if optional else ":")
            self.type_object(fieldtype)
            self.write(";")
        self.write("}")

    def field_with_type(self, name: str, obj: object) -> None:
        self.write(name, ":")
        self.type_object(obj)

    def method(self, method: Method) -> None:
        self.doc(method.implementation.__doc__)
        self.write(
            "export async function ", method.implementation.__name__, "(parameters: "
        )
        self.type_object(method.type)
        if (
            len([key for key in method.type_hints if key not in SPECIAL_PARAMETERS])
            == 0
        ):
            self.write(" = {}")
        self.write("):Promise<MethodResult<")
        self.type_object(method.type_hints["return"])
        self.write(">>{")
        self.write(
            "return await app.method(",
            repr(method.implementation.__name__),
            ", parameters);",
        )
        self.write("}\n")
