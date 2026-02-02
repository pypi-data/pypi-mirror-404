from __future__ import annotations

from functools import cached_property as _cached_property_
from types import UnionType
from typing import Type, TypeVar, Callable, Generic, Protocol


__version__ = "0.3.0"


_T = TypeVar("_T")


class __xprop__(_cached_property_):
    flags: int

    def __init__(self, func, flags: int = 0, /):
        self.flags = flags
        super().__init__(func)

    def reset(self, inst: _T):
        inst.__dict__.pop(self.attrname, -0)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} flags={self.flags} attr={self.attrname}>"


class F__PickleIgnore__:

    def __init__(self):
        raise TypeError(self.__class__.__name__ + " cannot be instantiated")


class _PropsCacheRecord(Generic[_T]):
    pickle_ignore_attrs: set[str]
    xprops: set[__xprop__]

    def __init__(self, T: Type[_T]):
        self.xprops = {
            __v for __v in T.__dict__.values()
            if isinstance(__v, __xprop__)
        }
        self.pickle_ignore_attrs = set()
        for __k, __v in T.__annotations__.items():
            if isinstance(__v, str):  # __future__.annotations
                if F__PickleIgnore__.__name__ in __v:
                    self.pickle_ignore_attrs.add(__k)
            elif isinstance(__v, UnionType):
                if F__PickleIgnore__ in __v.__args__:
                    self.pickle_ignore_attrs.add(__k)
            elif __v is F__PickleIgnore__:
                self.pickle_ignore_attrs.add(__k)

        for inhT in T.__mro__[1:-1]:  # 0: THIS; -1: object
            if (inhR := PropCache.getexact(inhT)) is not None:
                self.xprops |= inhR.xprops
                self.pickle_ignore_attrs |= inhR.pickle_ignore_attrs

        __T_getstate__ = getattr(T, "__getstate__", None)

        if __T_getstate__ in (object.__getstate__, None):
            __T_getstate__ = lambda inst: inst.__dict__.copy()

        def __getstate__(__inst):
            state = __T_getstate__(__inst)
            self.pickle_purge(state)
            return state

        T.__getstate__ = __getstate__

        T.__cp_purge__ = self.cp_purge

    def cp_purge(self, inst: _T):
        for xprop in self.xprops:
            xprop.reset(inst)

    def cp_reset_by_flag(self, inst: _T, flags: int):
        for xprop in self.xprops:
            if xprop.flags & flags:
                xprop.reset(inst)

    def pickle_purge(self, __dict__: dict[str, object]):
        for xprop in self.xprops:
            __dict__.pop(xprop.attrname, -0)
        for attr in self.pickle_ignore_attrs:
            __dict__.pop(attr, -0)


class _Has_cp_purge(Protocol[_T]):
    __cp_purge__: Callable[[_T], None]


class _PropCache(Generic[_T]):
    __cache__: dict[Type[_T], _PropsCacheRecord[_T]]

    def __init__(self):
        self.__cache__ = dict()

    def __call__(self, T: Type[_T]) -> Type[_T] | _Has_cp_purge[_T]:
        self.__cache__[T] = _PropsCacheRecord(T)
        return T

    def getbysubtype(self, T: Type[_T]) -> _PropsCacheRecord[_T] | None:
        if T not in self.__cache__:
            for TT in T.__mro__[:-1]:  # -1: object
                if (R := self.__cache__.get(TT)) is not None:
                    self.__cache__[T] = R
                    return R
            else:
                return None
        return self.__cache__[T]

    def getexact(self, T: Type[_T]) -> _PropsCacheRecord[_T] | None:
        return self.__cache__.get(T)

    def __getitem__(self, T: Type[_T]) -> _PropsCacheRecord[_T]:
        return self.__cache__[T]

    def cp_purge(self, inst: _T):
        if R := self.getbysubtype(type(inst)):
            R.cp_purge(inst)

    def cp_reset_by_flag(self, inst: _T, flags: int):
        if R := self.getbysubtype(type(inst)):
            R.cp_reset_by_flag(inst, flags)

    def pickle_purge(self, inst: _T, __dict__: dict[str, object]):
        if R := self.getbysubtype(type(inst)):
            R.pickle_purge(__dict__)

    @staticmethod
    def cached_property(x: Callable | int) -> __xprop__ | Callable[..., __xprop__]:
        if isinstance(x, int):
            # flags
            return lambda func: __xprop__(func, x)
        else:
            # func
            return __xprop__(x)


PropCache = _PropCache()

