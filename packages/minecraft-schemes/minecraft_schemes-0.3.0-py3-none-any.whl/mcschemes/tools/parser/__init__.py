# -*- encoding: utf-8 -*-
__all__ = (
    'Scheme',
    'SchemeLiteral',
    'parse',
    'loads',
    'load',
    'loadVersionAttrsFromClientJar',
    'converters',
    'createConverter'
)

import enum
import json
import os
from contextlib import nullcontext
from io import TextIOWrapper
from zipfile import BadZipFile
from zipfile import LargeZipFile
from zipfile import ZipFile

import cattrs
from typing_extensions import Any
from typing_extensions import IO
from typing_extensions import Literal
from typing_extensions import NamedTuple
from typing_extensions import TypeAlias
from typing_extensions import overload

from mcschemes.assetindex import AssetIndex
from mcschemes.clientmanifest import ClientManifest
from mcschemes.mojangjava import MojangJavaRuntimeIndex
from mcschemes.mojangjava import MojangJavaRuntimeManifest
from mcschemes.tools.parser import converters
from mcschemes.tools.parser.converters import createConverter as createConverter
from mcschemes.versionattrs import VersionAttributes
from mcschemes.versionmanifest import VersionManifest

_SchemeTargets: TypeAlias = (
        AssetIndex
        | ClientManifest
        | VersionManifest
        | VersionAttributes
        | MojangJavaRuntimeIndex
        | MojangJavaRuntimeManifest
)


class _SchemeAttribute(NamedTuple):
    target: type[_SchemeTargets]
    buildable: bool


@enum.unique
class Scheme(_SchemeAttribute, enum.Enum):
    VERSION_MANIFEST = (VersionManifest, False)
    CLIENT_MANIFEST = (ClientManifest, False)
    ASSET_INDEX = (AssetIndex, False)
    VERSION_ATTRIBUTES = (VersionAttributes, False)
    MOJANG_JAVA_RUNTIME_INDEX = (MojangJavaRuntimeIndex, False)
    MOJANG_JAVA_RUNTIME_MANIFEST = (MojangJavaRuntimeManifest, False)


SchemeLiteral: TypeAlias = Literal[
    Scheme.VERSION_MANIFEST,
    Scheme.CLIENT_MANIFEST,
    Scheme.ASSET_INDEX,
    Scheme.VERSION_ATTRIBUTES,
    Scheme.MOJANG_JAVA_RUNTIME_INDEX,
    Scheme.MOJANG_JAVA_RUNTIME_MANIFEST
]


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.ASSET_INDEX], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> AssetIndex: ...


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.CLIENT_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> ClientManifest: ...


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.VERSION_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> VersionManifest: ...


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.VERSION_ATTRIBUTES], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> VersionAttributes: ...


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.MOJANG_JAVA_RUNTIME_INDEX], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> MojangJavaRuntimeIndex: ...


@overload
def parse(
        obj: Any,
        scheme: Literal[Scheme.MOJANG_JAVA_RUNTIME_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...
) -> MojangJavaRuntimeManifest: ...


def parse(
        obj: Any,
        scheme: Any, /,
        *, converter: cattrs.BaseConverter | None = None
) -> Any:
    if scheme not in Scheme:
        raise TypeError(
                'Scheme must be one member of the enum {0.__module__}.{0.__name__}, '
                'but {1!r} ({2.__qualname__} object) is not'.format(
                        Scheme, obj, type(obj)
                )
        )
    cl = scheme.target

    if converter is None:
        converter = converters.DedicatedConverter()
    elif not isinstance(converter, cattrs.BaseConverter):
        raise TypeError(
                '{0!r} must be a {1.__module__}.{1.__name__} object, '
                'a {2.__module__}.{2.__name__} object or None '
                '(got {3!r} that is {4.__qualname__!s} object)'.format(
                        'converter', cattrs.Converter, cattrs.BaseConverter, converter, type(converter)
                )
        )

    return converter.structure(obj, cl)


@overload
def loads(
        s: str,
        scheme: Literal[Scheme.ASSET_INDEX], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_loads_kwargs: Any
) -> AssetIndex: ...


@overload
def loads(
        s: str,
        scheme: Literal[Scheme.CLIENT_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_loads_kwargs: Any
) -> ClientManifest: ...


@overload
def loads(
        s: str,
        scheme: Literal[Scheme.VERSION_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_loads_kwargs: Any
) -> VersionManifest: ...


def loads(
        s: str,
        scheme: Any, /,
        *, converter: cattrs.BaseConverter | None = None,
        **json_loads_kwargs: Any
) -> Any:
    return parse(json.loads(s, **json_loads_kwargs), scheme, converter=converter)


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.ASSET_INDEX], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> AssetIndex: ...


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.CLIENT_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> ClientManifest: ...


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.VERSION_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> VersionManifest: ...


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.VERSION_ATTRIBUTES], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> VersionAttributes: ...


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.MOJANG_JAVA_RUNTIME_INDEX], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> MojangJavaRuntimeIndex: ...


@overload
def load(
        fp: IO[str],
        scheme: Literal[Scheme.MOJANG_JAVA_RUNTIME_MANIFEST], /,
        *, converter: cattrs.BaseConverter | None = ...,
        **json_load_kwargs: Any
) -> MojangJavaRuntimeManifest: ...


def load(
        fp: IO[str],
        scheme: Any, /,
        *, converter: cattrs.BaseConverter | None = None,
        **json_load_kwargs: Any
) -> Any:
    return parse(json.load(fp, **json_load_kwargs), scheme, converter=converter)


def loadVersionAttrsFromClientJar(
        file: str | os.PathLike[str] | IO[bytes], /,
        *, converter: cattrs.BaseConverter | None = None,
        **json_loads_kwargs: Any
) -> VersionAttributes:
    if isinstance(file, str):
        fp_ctx = open(file, mode='rb')
    else:
        fp_ctx = nullcontext(file)  # type: ignore[assignment]

    with fp_ctx as fp:
        with ZipFile(fp, mode='r') as zfp:
            try:
                version_json_member_fp = zfp.open('version.json', mode='r')
            except (KeyError, BadZipFile, LargeZipFile):
                raise

            with TextIOWrapper(version_json_member_fp, encoding='utf-8') as version_json_fp:
                return load(version_json_fp, Scheme.VERSION_ATTRIBUTES, converter=converter, **json_loads_kwargs)
