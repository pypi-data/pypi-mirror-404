# -*- encoding: utf-8 -*-
__all__ = (
    'VersionAttributes',
    'nodes'
)

import attrs
from pendulum import DateTime

from mcschemes.versionattrs import nodes


@attrs.define(kw_only=True, slots=True)
class VersionAttributes:
    """
    This class is represented the structure of the ``version.json``.

    ``version.json`` is embedded within ``client.jar`` in ``.minecraft/versions/<version>``
    and ``server.jar`` since 18w47b. It offers some basic information about the version's attributes.

    See Also: https://zh.minecraft.wiki/w/%E7%89%88%E6%9C%AC%E4%BF%A1%E6%81%AF%E6%96%87%E4%BB%B6%E6%A0%BC%E5%BC%8F
    """
    # Required attributes (but may not exist in the version.json)
    build_time: DateTime
    """The build time of this version in ISO 8601 format."""
    id: str
    """
    The version's unique identifier. May sometimes display the build hash as well,
    separated from the name by a slash.
    """
    name: str
    """The version's user-friendly name. Usually identical to ``id``."""
    pack_version: nodes.PackFormatVersion
    """
    The resource and data pack formats version of this version.
    
    See ``mcschemes.versionattrs.nodes.PackFormatVersion``,
    ``mcschemes.versionattrs.nodes.PackFormatVersionCurrent``,
    ``mcschemes.versionattrs.nodes.PackFormatVersionBefore25w31a``
    and ``mcschemes.versionattrs.nodes.PackFormatVersionBefore20w45a`` for more information.
    """
    protocol_version: int
    """The protocol version of this version."""
    stable: bool
    """Whether this version is a release version (``True``) or a development version (``False``)."""
    world_version: int
    """The data version of this version."""

    # Optional attributes
    java_component: str | None = None
    """The codename of Java component used for this version."""
    java_version: int | None = None
    """The Java version used for this version."""
    release_target: str | None = None
    """The target release version of this version. Removed since 22w42a."""
    use_editor: bool | None = None
    """Unknown use. Added in 23w31a."""
    series_id: str | None = None
    """
    Identifies which branch the version is from.

    The default value is ``main`` and other values are used
    when a version isn't from the main branch. For example:

    - ``ccpreview``: Was used for 1.18 Experimental Snapshot 1
    - ``deep_dark_preview``: Was used for Deep Dark Experimental Snapshot 1
    - ``april<YYYY>``: Is used for April Fools' Day joke versions released in 2022 or after.

    This is also used as a secondary way from the data version (``world_version``)
    to check for incompatibility.
    
    Added in 21w37a.
    """
