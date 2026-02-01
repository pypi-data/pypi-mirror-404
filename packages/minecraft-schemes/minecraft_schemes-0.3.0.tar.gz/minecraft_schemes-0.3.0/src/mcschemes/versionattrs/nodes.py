# -*- encoding: utf-8 -*-
__all__ = (
    'PackFormatVersion',
    'PackFormatVersionCurrent',
    'PackFormatVersionBefore25w31a',
    'PackFormatVersionBefore20w45a'
)

import attrs
from typing_extensions import TypeAlias

PackFormatVersionBefore20w45a: TypeAlias = int
"""
An integer representing the resource and data pack format version,
until the snapshot 20w45a.
"""


@attrs.define(kw_only=True, slots=True)
class PackFormatVersionBefore25w31a:
    """The resource and data pack format version, until the snapshot 25w31a."""
    data: int
    """An integer representing the data pack format version."""
    resource: int
    """An integer representing the resource pack format version."""


@attrs.define(kw_only=True, slots=True)
class PackFormatVersionCurrent:
    """The resource and data pack format version, since the snapshot 25w31a."""
    data_major: int
    """An integer representing the major data pack format version."""
    data_minor: int
    """An integer representing the minor data pack format version."""
    resource_major: int
    """An integer representing the major resource pack format version."""
    resource_minor: int
    """An integer representing the minor resource pack format version."""


PackFormatVersion: TypeAlias = (
        PackFormatVersionCurrent
        | PackFormatVersionBefore25w31a
        | PackFormatVersionBefore20w45a
)
"""A type alias for declarations of all supported pack format version structures."""
