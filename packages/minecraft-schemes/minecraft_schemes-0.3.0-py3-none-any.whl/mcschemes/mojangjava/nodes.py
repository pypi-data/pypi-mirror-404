# -*- encoding: utf-8 -*-
__all__ = (
    'PlatformClassifier',
    'JavaRuntimeCodename',
    'RelativePath',
    'JavaRuntimeFileCompression',
    'JavaRuntimeVersion',
    'Availability',
    'ManifestFileInfo',
    'IndexEntity',
    'PathType',
    'DirectoryPathInfo',
    'FilePathInfo',
    'SymlinkPathInfo',
    'FileDownloadInfo'
)

from enum import StrEnum
from pathlib import Path

import attrs
from pendulum import DateTime
from typing_extensions import Literal
from typing_extensions import TypeAlias

from mcschemes.specials import Sha1Sum

PlatformClassifier: TypeAlias = str
JavaRuntimeCodename: TypeAlias = str
RelativePath: TypeAlias = Path
JavaRuntimeFileCompression: TypeAlias = str


@attrs.define(kw_only=True, slots=True)
class JavaRuntimeVersion:
    name: str
    released: DateTime


@attrs.define(kw_only=True, slots=True)
class Availability:
    group: int
    progress: int


@attrs.define(kw_only=True, slots=True)
class ManifestFileInfo:
    sha1: Sha1Sum
    size: int
    url: str


@attrs.define(kw_only=True, slots=True)
class IndexEntity:
    availability: Availability
    version: JavaRuntimeVersion
    manifest: ManifestFileInfo


class PathType(StrEnum):
    DIRECTORY = 'directory'
    FILE = 'file'
    LINK = 'link'


@attrs.define(kw_only=True, slots=True)
class DirectoryPathInfo:
    type: Literal[PathType.DIRECTORY]


@attrs.define(kw_only=True, slots=True)
class FileDownloadInfo:
    sha1: Sha1Sum
    size: int
    url: str


@attrs.define(kw_only=True, slots=True)
class FilePathInfo:
    type: Literal[PathType.FILE]
    executable: bool
    downloads: dict[JavaRuntimeFileCompression, FileDownloadInfo]


@attrs.define(kw_only=True, slots=True)
class SymlinkPathInfo:
    type: Literal[PathType.LINK]
    target: Path
