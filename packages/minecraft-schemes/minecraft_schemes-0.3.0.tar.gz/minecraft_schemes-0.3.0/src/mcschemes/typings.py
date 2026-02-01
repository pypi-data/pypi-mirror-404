# -*- encoding: utf-8 -*-
__all__ = (
    'SupportsCustomStructure',
    'SupportsCustomUnstructure',
    'SupportsGetBuffer',
    'SupportsReadInto'
)

from abc import abstractmethod
from collections.abc import Buffer

import cattrs
from typing_extensions import Any
from typing_extensions import Protocol
from typing_extensions import runtime_checkable


@runtime_checkable
class SupportsCustomStructure(Protocol):
    @classmethod
    @abstractmethod
    def __structure__(cls, converter: cattrs.Converter, value: Any, /) -> Any:
        raise NotImplementedError


@runtime_checkable
class SupportsCustomUnstructure(Protocol):
    @abstractmethod
    def __unstructure__(self, converter: cattrs.Converter, /) -> Any:
        raise NotImplementedError


class SupportsGetBuffer(Protocol):
    def getbuffer(self) -> Buffer: ...


class SupportsReadInto(Protocol):
    def readinto(self, buffer: bytearray, /) -> int: ...

    def readable(self) -> bool: ...
