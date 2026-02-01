# -*- encoding: utf-8 -*-
__all__ = (
    'ClientManifest',
    'nodes'
)

import attrs
from pendulum import DateTime

from mcschemes.clientmanifest import nodes
from mcschemes.enums import VersionTypeLiteral


@attrs.define(kw_only=True, slots=True)
class ClientManifest:
    arguments: nodes.Arguments | None = None
    """
    Contains game and JVM arguments. Replaced ``minecraftArguments`` since 17w43a.

    See documentation of ``mcschemes.clientmanifest.nodes.Arguments``.
    """
    assetIndex: nodes.AssetIndexFileInfo
    """See documentation of ``mcschemes.clientmanifest.nodes.AssetIndexFileInfo``."""
    assets: str
    """The assets version."""
    complianceLevel: int = 0
    """
    The level of player safety features supports, used for the official launcher.

    If appeared, a value of ``0`` causes the official launcher to warn the player about missing player safety features when this version is selected.

    This value is usually ``1`` after 1.16.4-pre2.
    """
    downloads: dict[str, nodes.CoreFileInfo]
    """
    A mapping contains download information about client, server and obfuscation maps,
    among other information. Frequently appearing keys:

    - ``client`` - The client.jar download information.
    - ``client_mappings`` - The obfuscation maps for this client version.
      Added in Java Edition 19w36a but got included in 1.14.4 also.
    - ``server`` - The server download information.
    - ``server_mappings`` - The obfuscation maps for this server version.
      Added in Java Edition 19w36a but got included in 1.14.4 also.
    - ``windows_server`` - The Windows server download information.
      Removed in Java Edition 16w05a, but is still present in prior versions.

    All values are ``mcschemes.clientmanifest.nodes.CoreFileInfo`` instances.
    """
    id: str
    """The name of this version client (e.g. 1.14.4)."""
    javaVersion: nodes.JavaVersionInfo | None = None
    """See documentation of ``mcschemes.clientmanifest.nodes.JavaVersionInfo``."""
    libraries: list[nodes.LibraryDependencyInfo]
    """A list of library dependencies."""
    logging: dict[str, nodes.Log4JConfigInfo]
    """Information about Log4j log configuration."""
    mainClass: str
    """
    The main game class. For modern versions, it is ``net.minecraft.client.main.Main``,
    but it may differ for older or ancient versions.
    """
    minecraftArguments: str | None = None
    """A string contains arguments passed to the game. Replaced by ``arguments`` since 17w43a."""
    minimumLauncherVersion: int | None = None
    """The minimum official launcher version that can run this version of the game."""
    releaseTime: DateTime
    """The release date-time in ISO-8601 extended offset format."""
    time: DateTime
    """The update date-time in ISO-8601 extended offset format."""
    type: VersionTypeLiteral
    """
    The type of this game version. Can be one of enumeration members:

    - ``mcschemes.enums.VersionType.RELEASE``
    - ``mcschemes.enums.VersionType.SNAPSHOT``
    - ``mcschemes.enums.VersionType.OLD_BETA``
    - ``mcschemes.enums.VersionType.OLD_ALPHA``
    """
