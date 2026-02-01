# -*- encoding: utf-8 -*-
__all__ = (
    'VersionType',
    'VersionTypeLiteral',
    'RuleAction',
    'RuleActionLiteral'
)

from enum import StrEnum

from typing_extensions import Literal
from typing_extensions import TypeAlias


class VersionType(StrEnum):
    RELEASE = 'release'
    SNAPSHOT = 'snapshot'
    OLD_BETA = 'old_beta'
    OLD_ALPHA = 'old_alpha'


VersionTypeLiteral: TypeAlias = Literal[
    VersionType.RELEASE,
    VersionType.SNAPSHOT,
    VersionType.OLD_BETA,
    VersionType.OLD_ALPHA
]


class RuleAction(StrEnum):
    ALLOW = 'allow'
    DISALLOW = 'disallow'


RuleActionLiteral: TypeAlias = Literal[
    RuleAction.ALLOW,
    RuleAction.DISALLOW
]
