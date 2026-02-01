# -*- encoding: utf-8 -*-
__all__ = (
    'AssetIndexFileInfo',
    'CoreFileInfo',
    'Log4JConfigFileInfo',
    'Log4JConfigInfo',
    'RuleOSEntry',
    'RuleEntry',
    'ArgumentEntry',
    'Arguments',
    'LibraryDependencyMavenInfo',
    'LibraryDependencyFileInfo',
    'LibraryDependencyFileExtractInfo',
    'LibraryDependencyInfo',
    'JavaVersionInfo'
)

import re

import attrs
import cattrs
from typing_extensions import Any
from typing_extensions import NamedTuple
from typing_extensions import Self

from mcschemes.enums import RuleActionLiteral
from mcschemes.specials import Sha1Sum


@attrs.define(kw_only=True, slots=True)
class AssetIndexFileInfo:
    id: str
    """The assetindex version."""
    sha1: Sha1Sum
    """The SHA-1 hash of the asset index file."""
    size: int
    """The size of the asset index file in bytes."""
    totalSize: int
    """The total size of all asset files."""
    url: str
    """The URL that the game/launcher should visit to download the asset index file."""


@attrs.define(kw_only=True, slots=True)
class CoreFileInfo:
    sha1: Sha1Sum
    """The SHA-1 hash of the core file."""
    size: int
    """The size of the core file."""
    url: str
    """The URL that the launcher should visit to download the core file."""


@attrs.define(kw_only=True, slots=True)
class Log4JConfigFileInfo:
    id: str
    """
    The filename of the log4j configuration file.

    Its value is usually ``client-1.12.xml``, but may differ for older versions.
    """
    sha1: Sha1Sum
    """The SHA-1 hash of the log4j configuration file."""
    size: int
    """The size of the log4j configuration file in bytes."""
    url: str
    """The URL that the launcher should visit to download the log4j configuration file."""


@attrs.define(kw_only=True, slots=True)
class Log4JConfigInfo:
    argument: str
    """
    The JVM argument for adding the log4j configuration.
    Its value is usually ``-Dlog4j.configurationFile=${path}``.
    """
    type: str
    """The type of the log4j configuration file. Its value is usually ``log4j2-xml``."""
    file: Log4JConfigFileInfo
    """
    The Log4j2 XML configuration used by this version
    for the launcher for launcher's log screen.
    """


@attrs.define(kw_only=True, slots=True)
class RuleOSEntry:
    name: str | None = None
    """
    An identifier for the current operating system.
    Should be one of ``windows``, ``osx`` or ``linux``.
    """
    version: re.Pattern[str] | None = None
    """
    A regex intended to be checked against
    ``System.getProperty("os.version")`` (Java),
    ``platform.version()`` (Python for Windows)
    or ``platform.release()`` (Python for other platforms, maybe included macOS).
    """
    arch: str | None = None
    """
    An identifier for the architecture of the current operating system.
    Frequently appearing values: ``x86``.
    """


@attrs.define(kw_only=True, slots=True)
class RuleEntry:
    action: RuleActionLiteral
    """
    The action when the rule satisfied. Can be one of enumeration members:
    ``mcschemes.enums.RuleAction.ALLOW`` or ``mcschemes.enums.RuleAction.DISALLOW``.
    If the remaining conditions are met, this action should be executed.
    """
    features: dict[str, bool] = attrs.field(factory=dict)
    """
    Includes a set of features that can be checked by the launcher.
    Frequently appearing features (as the key of this mapping):
    
    - ``is_demo_user``
    - ``has_custom_resolution``
    - ``has_quick_plays_support``
    - ``is_quick_play_singleplayer``
    - ``is_quick_play_multiplayer``
    - ``is_quick_play_realms``
    """
    os: RuleOSEntry | None = None
    """See documentation of ``mcschemes.clientmanifest.nodes.RuleOSEntry``."""


@attrs.define(kw_only=True, slots=True)
class ArgumentEntry:
    value: list[str]
    """An argument or a list of arguments that is added when the condition is matched."""
    rules: list[RuleEntry] = attrs.field(factory=list)
    """
    A list of conditions to be checked.

    For the condition checking, see documentation of
    ``mcschemes.clientmanifest.nodes.RuleEntry`` and help functions
    ``isAllowed()``, ``isTotallyAllowed()``,
    ``isArgumentCanBeAppended()`` and ``isLibraryDependencyCanBeAppended()``
    in the module ``mcschemes.tools.rules``.
    """

    @classmethod
    def __structure__(cls, converter: cattrs.Converter, value: str | dict[str, Any], /) -> Self:
        if isinstance(value, str):
            return cls(value=[value])
        elif isinstance(value, dict):
            if isinstance(value['value'], str):
                cmdargs = [value['value']]
            else:
                cmdargs = list(value['value'])
            rules = converter.structure(value['rules'], list[RuleEntry])

            return cls(value=cmdargs, rules=rules)

        raise TypeError('Cannot structure value {0!r} to {1.__qualname__!r} instance'.format(value, cls))


@attrs.define(kw_only=True, slots=True)
class Arguments:
    game: list[ArgumentEntry]
    """
    Contains arguments supplied to the game, such as
    information about the username and the version.
    
    For the sake of simplicity, all arguments will be
    structured as/wrapped into
    ``mcschemes.clientmanifest.nodes.ArgumentEntry`` instances.
    """  # TODO: more detailed description for simplify operations
    jvm: list[ArgumentEntry]
    """
    Contains JVM arguments, such as information about
    memory allocation, garbage collector selection, or environment variables.
    
    For the sake of simplicity, all arguments will be
    structured as/wrapped into
    ``mcschemes.clientmanifest.nodes.ArgumentEntry`` instances.
    """


class LibraryDependencyMavenInfo(NamedTuple):
    groupId: str
    artifactId: str
    version: str


@attrs.define(kw_only=True, slots=True)
class LibraryDependencyFileInfo:
    path: str
    """Path to store the downloaded artifact/classifier file, relative to the directory ``.minecraft/libraries``."""
    sha1: Sha1Sum
    """The SHA1 hash of the artifact/classifier file."""
    size: int
    """The size of the artifact/classifier file in bytes."""
    url: str
    """The URL that the game/launcher should visit to download the file."""


@attrs.define(kw_only=True, slots=True)
class LibraryDependencyFileExtractInfo:
    exclude: list[str] = attrs.field(factory=list)
    """Paths to exclude when extracting artifact/classifier files."""


@attrs.define(kw_only=True, slots=True)
class LibraryDependencyInfo:
    name: str
    """A maven name for the library, in the form of `groupId:artifactId:version`."""
    artifact: LibraryDependencyFileInfo | None = None
    """Info about the artifact."""
    classifiers: dict[str, LibraryDependencyFileInfo] = attrs.field(factory=dict)
    """
    Specifies the artifact information for the artifact with this specific classifier.
    
    Keys in this mapping will also appears in values of ``natives`` mapping.
    The structure of values in this mapping are same with ``artifact``.
    """
    natives: dict[str, str] = attrs.field(factory=dict)
    """
    Information about native libraries (in C) bundled with this library.
    Fills only when there are classifiers for natives.
    """  # TODO: more detailed description for keys and values
    extract: LibraryDependencyFileExtractInfo | None = None
    """Rules to follow when extracting natives from a library."""
    rules: list[RuleEntry] = attrs.field(factory=list)
    """
    A list of conditions to be checked.

    For the condition checking, see documentation of
    ``mcschemes.clientmanifest.nodes.RuleEntry`` and help functions
    ``isAllowed()``, ``isTotallyAllowed()``,
    ``isArgumentCanBeAppended()`` and ``isLibraryDependencyCanBeAppended()``
    in the module ``mcschemes.tools.rules``.
    """

    def splitLibraryName(self) -> LibraryDependencyMavenInfo:
        """Split the library name in the form of `groupId:artifactId:version`."""
        split = self.name.split(':', maxsplit=2)

        if len(split) < 3:
            raise ValueError('Cannot split an invalid library name: {0!r}'.format(self.name))

        return LibraryDependencyMavenInfo(*split)


@attrs.define(kw_only=True, slots=True)
class JavaVersionInfo:
    component: str
    """
    The codename of the preferred Java Runtime Environment provided by Mojang to use.
    Frequently appearing values:

    - ``jre-legacy`` until 21w18a
    - ``java-runtime-alpha`` until 1.18-pre1
    - ``java-runtime-beta`` until 22w17a
    - ``java-runtime-gamma`` until 24w13a
    - ``java-runtime-delta`` until 24w14a
    """
    majorVersion: int
    """
    The major version of the required Java Runtime Environment.
    Its value is ``8`` until 21w18a, ``16`` until 1.18-pre1,
    ``17`` until 24w13a, and ``21`` since 24w14a.
    """
