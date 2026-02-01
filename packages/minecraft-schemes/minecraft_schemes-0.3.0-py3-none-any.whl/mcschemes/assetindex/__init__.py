# -*- encoding: utf-8 -*-
__all__ = (
    'AssetIndex',
    'nodes'
)

from pathlib import Path

import attrs
from typing_extensions import TypeAlias

from mcschemes.assetindex import nodes

AssetFileRelativePath: TypeAlias = Path


@attrs.define(kw_only=True, slots=True)
class AssetIndex:
    objects: dict[AssetFileRelativePath, nodes.AssetFileEntry]
    """
    A mapping of asset files.
    The key of the mapping is relative path to asset files
    under ``.minecraft/assets/`` in ``pathlib.Path`` object,
    and the value is ``mcschemes.assetindex.nodes.AssetFileEntry`` object.
    """
    virtual: bool | None = None
    map_to_resources: bool | None = None
