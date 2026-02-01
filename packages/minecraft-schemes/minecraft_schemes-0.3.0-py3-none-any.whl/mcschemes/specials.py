# -*- encoding: utf-8 -*-
__all__ = (
    'Sha1Sum',
    'ChecksumMismatch'
)

import operator
from dataclasses import dataclass
from functools import partial
from hashlib import file_digest

import attrs
from typing_extensions import Annotated
from typing_extensions import Any
from typing_extensions import Self

from mcschemes.typings import SupportsGetBuffer
from mcschemes.typings import SupportsReadInto


@dataclass(frozen=True, slots=True)
class _ExactLength:
    length: Annotated[int, partial(operator.eq, 0)]


@attrs.frozen(kw_only=True, slots=True)
class ChecksumMismatch(Exception):
    expected: 'Sha1Sum'
    actual: 'Sha1Sum'


@attrs.frozen(
        slots=True,
        repr=False,
        eq=False,  # To allow case-insensitive hexdigest-based comparison
        unsafe_hash=True
        # Force attrs generate a __hash__(),
        # otherwise attrs will not generate it by default
        # and this behavior is unexpected in this case
)
class Sha1Sum:
    hexdigest: Annotated[str, _ExactLength(40)] = attrs.field(
            validator=attrs.validators.and_(
                    attrs.validators.instance_of(str),
                    attrs.validators.min_len(40),
                    attrs.validators.max_len(40)
            )
    )

    def __repr__(self) -> str:
        return f'{type(self).__qualname__!s}({self.hexdigest!r})'

    def __str__(self) -> str:
        return str(self.hexdigest)

    def __eq__(self, other: Any, /) -> bool:
        if isinstance(other, type(self)):
            return self.hexdigest.lower() == other.hexdigest.lower()

        return NotImplemented

    @classmethod
    def fromFile(cls, fp: SupportsGetBuffer | SupportsReadInto, /) -> Self:
        return cls(file_digest(fp, 'sha1').hexdigest())

    def checkFile(self, fp: SupportsGetBuffer | SupportsReadInto, /) -> None:
        other_sha1sum = self.fromFile(fp)
        if self != other_sha1sum:
            raise ChecksumMismatch(expected=self, actual=other_sha1sum)
