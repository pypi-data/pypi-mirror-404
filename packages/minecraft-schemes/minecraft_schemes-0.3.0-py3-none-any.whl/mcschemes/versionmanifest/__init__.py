# -*- encoding: utf-8 -*-
__all__ = (
    'VersionManifest',
    'nodes'
)

import attrs

from mcschemes.versionmanifest import nodes


@attrs.define(kw_only=True, slots=True)
class VersionManifest:
    latest: nodes.LatestReleaseTypeOfVersion
    """The ID of latest release and snapshot versions."""
    versions: list[nodes.VersionEntry]
    """A list of versions available."""
