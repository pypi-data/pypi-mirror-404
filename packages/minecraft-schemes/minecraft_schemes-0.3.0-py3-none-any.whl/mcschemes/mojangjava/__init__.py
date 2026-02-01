# -*- encoding: utf-8 -*-
__all__ = (
    'MojangJavaRuntimeIndex',
    'MojangJavaRuntimeManifest',
    'nodes'
)

import attrs
from typing_extensions import TypeAlias

from mcschemes.mojangjava import nodes

MojangJavaRuntimeIndex: TypeAlias = dict[
    nodes.PlatformClassifier,
    dict[
        nodes.JavaRuntimeCodename,
        list[nodes.IndexEntity]
    ]
]
"""
The index of manifests for Mojang provided Java Runtime, including availability,
version and manifest file download information.

Since Mojang or Minecraft Wiki does not provide a description or specification for this file,
the structure declaration provided by this module may not be accurate enough,
and may contain some errors.

You can find this index file at: https://piston-meta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json

For information about the manifest file, see ``mcschemes.mojangjava.MojangJavaRuntimeManifest``.
"""


@attrs.define(kw_only=True, slots=True)
class MojangJavaRuntimeManifest:
    """
    The manifest for Mojang provided Java Runtime, including paths
    for every file/directory/symbolic link belongs to the runtime.
    For files, information such as their download URL is also provided.

    Since Mojang or Minecraft Wiki does not provide a description or specification for this file,
    the structure declaration provided by this module may not be accurate enough,
    and may contain some errors.
    """
    files: dict[nodes.RelativePath, nodes.DirectoryPathInfo | nodes.FilePathInfo | nodes.SymlinkPathInfo]
