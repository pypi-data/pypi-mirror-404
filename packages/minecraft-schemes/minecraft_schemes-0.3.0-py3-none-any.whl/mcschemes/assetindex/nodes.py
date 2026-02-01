# -*- encoding: utf-8 -*-
__all__ = (
    'AssetFileEntry',
)

import attrs

from mcschemes.specials import Sha1Sum


@attrs.define(kw_only=True, slots=True)
class AssetFileEntry:
    hash: Sha1Sum
    """The SHA-1 hash of this asset file."""
    size: int
    """The size of this asset file."""
