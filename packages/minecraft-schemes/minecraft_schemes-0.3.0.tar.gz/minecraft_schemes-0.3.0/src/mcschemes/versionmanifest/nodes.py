# -*- encoding: utf-8 -*-
__all__ = (
    'VersionEntry',
    'LatestReleaseTypeOfVersion'
)

import attrs
from pendulum import DateTime

from mcschemes.enums import VersionTypeLiteral
from mcschemes.specials import Sha1Sum


@attrs.define(kw_only=True, slots=True)
class VersionEntry:
    id: str
    """The ID of this version."""
    type: VersionTypeLiteral
    """The type of this version; should be a member of enum ``mcschemes.enums.VersionType``."""
    url: str
    """The link to the ``<NodeVersionEntry.id>.json`` for this version."""
    time: DateTime
    """A timestamp in ISO 8601 format of when the version files were last updated on the manifest."""
    releaseTime: DateTime
    """The release time of this version in ISO 8601 format."""
    sha1: Sha1Sum | None = None
    """
    The SHA-1 hash of the version and therefore the JSON file ID.

    **Availability:** Only in version_manifest_v2.json.
    """
    complianceLevel: int | None = None
    """
    The level of player safety features supports, used for the official launcher.

    If appeared, a value of ``0`` causes the official launcher to warn the player about missing player safety features when this version is selected.

    This value is usually ``1`` after 1.16.4-pre2.

    **Availability:** Only in version_manifest_v2.json.
    """


@attrs.define(kw_only=True, slots=True)
class LatestReleaseTypeOfVersion:
    release: str
    """The ID of the latest release version."""
    snapshot: str
    """The ID of the latest snapshot version."""
