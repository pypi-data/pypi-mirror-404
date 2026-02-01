# -*- encoding: utf-8 -*-
__all__ = (
    'isAllowed',
    'isTotallyAllowed',
    'isArgumentCanBeAppended',
    'isLibraryDependencyCanBeAppended'
)

import platform
import sys
from collections.abc import Iterable
from collections.abc import Mapping
from functools import partial

from mcschemes.clientmanifest.nodes import ArgumentEntry
from mcschemes.clientmanifest.nodes import LibraryDependencyInfo
from mcschemes.clientmanifest.nodes import RuleEntry
from mcschemes.enums import RuleAction

if sys.platform == 'linux':
    getOSVersion = platform.release
else:
    getOSVersion = platform.version


def getOSIdentifier(*, fallback: str = 'linux') -> str:
    match sys.platform:
        case 'win32' | 'cygwin':
            return 'windows'
        case 'darwin':
            return 'osx'
        case 'linux':
            return 'linux'
        case _:
            return fallback


def isSupports64Bits() -> bool:
    return sys.maxsize > 2 ** 32


def isAllowed(
        rule: RuleEntry, /,
        *, features: Mapping[str, bool] | None = None,
        os_id_fallback: str = 'linux'
) -> bool:
    if rule.features:
        if features is None:
            return False
        for expected_feature_name, expected_feature_flag in rule.features.items():
            if expected_feature_name in features:
                if expected_feature_flag == features[expected_feature_name]:
                    continue
            return False

    if rule.os:
        if rule.os:
            if rule.os.name != getOSIdentifier(fallback=os_id_fallback):
                return False
            if rule.os.arch and rule.os.arch == 'x86' and isSupports64Bits():
                return False
            if rule.os.version and not rule.os.version.fullmatch(getOSVersion()):
                return False

    return rule.action is RuleAction.ALLOW


def isTotallyAllowed(
        rules: Iterable[RuleEntry], /,
        *, features: Mapping[str, bool] | None = None,
        os_id_fallback: str = 'linux'
) -> bool:
    predicate = partial(isAllowed, features=features, os_id_fallback=os_id_fallback)
    return all(map(predicate, rules))


def isArgumentCanBeAppended(
        argument_entry: ArgumentEntry, /,
        *, features: Mapping[str, bool] | None = None,
        os_id_fallback: str = 'linux'
) -> bool:
    if argument_entry.rules:
        return isTotallyAllowed(argument_entry.rules, features=features, os_id_fallback=os_id_fallback)
    # Argument can be appended unconditionally when argument_entry.rules is empty
    return True


def isLibraryDependencyCanBeAppended(
        lib_dep_info: LibraryDependencyInfo, /,
        *, features: Mapping[str, bool] | None = None,
        os_id_fallback: str = 'linux'
) -> bool:
    if lib_dep_info.rules:
        return isTotallyAllowed(lib_dep_info.rules, features=features, os_id_fallback=os_id_fallback)
    # Library dependency can be appended unconditionally when lib_dep_info.rules is empty
    return True
