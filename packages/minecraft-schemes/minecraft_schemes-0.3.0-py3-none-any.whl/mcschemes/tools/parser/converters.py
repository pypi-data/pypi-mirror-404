# -*- encoding: utf-8 -*-
__all__ = (
    'DedicatedConverter',
    'createConverter'
)

import collections.abc
import re
from typing import TypeVar
from warnings import deprecated

import cattrs.preconf.json
from pendulum import Date
from pendulum import DateTime

from mcschemes.specials import Sha1Sum
from mcschemes.typings import SupportsCustomStructure
from mcschemes.typings import SupportsCustomUnstructure

_ConverterT = TypeVar('_ConverterT', bound=cattrs.BaseConverter)


class DedicatedConverter(cattrs.Converter):
    @classmethod
    def configure(cls, converter: _ConverterT, /, *, regex_flags: int | re.RegexFlag = 0) -> _ConverterT:
        """
        Configure an existing converter to convert some specific types.

        Specifically, hooks will be added for converting the following types:

        - All hooks added via ``cattrs.preconf.json.configure_converter()``.
        - ``DateTime`` and ``Date`` from package ``pendulum``: will be unserialized from string in ISO-8601 format
          and serialized to string in ISO-8601 format; override datetime hooks added by
          ``cattrs.preconf.json.configure_converter()``.
        - ``re.Pattern``: will be unserialized from string by ``re.compile()`` with the specified ``regex_flags``
          and serialized to string.
        - ``mcschemes.specials.Sha1Sum``: will be unserialized from hexadecimal string of length 40
          and serialized to lower-case hexadecimal string.
        - Any type defined special method ``__structure__()`` and/or ``__unstructure__()``.

        Args:
            converter (cattrs.Converter or cattrs.BaseConverter):
                The converter instance to configure.
            regex_flags (int | re.RegexFlag, optional):
                Regular expression flags to use when structuring regex pattern from string.

        Returns:
            The given ``converter`` with configurations.
        """
        if not isinstance(converter, cattrs.BaseConverter):
            raise TypeError(
                    'Expected an instance of {0.__module__}.{0.__name__} or its subclass, '
                    'but {1!r} ({2.__qualname__} object) is given'.format(cattrs.BaseConverter, converter, type(converter))
            )

        cattrs.preconf.json.configure_converter(converter)

        # pendulum.Date and pendulum.DateTime (un-)structing support
        converter.register_structure_hook(Date, lambda value, cls_: cls_.fromisoformat(value))
        converter.register_unstructure_hook(Date, lambda value: value.isoformat())
        converter.register_structure_hook(DateTime, lambda value, cls_: cls_.fromisoformat(value))
        converter.register_unstructure_hook(DateTime, lambda value: value.isoformat())

        # Custom (un-)structuring supports
        converter.register_structure_hook(SupportsCustomStructure, lambda value, cls_: cls_.__structure__(converter, value))
        converter.register_unstructure_hook(SupportsCustomUnstructure, lambda value: value.__unstructure__(converter))

        # re.Pattern support
        converter.register_structure_hook(re.Pattern, lambda value, cls_: re.compile(value, flags=regex_flags))
        converter.register_unstructure_hook(re.Pattern, lambda value: value.pattern)

        # mcschemes.specials.Sha1Sum support
        converter.register_structure_hook(Sha1Sum, lambda value, cls_: cls_(value))
        converter.register_unstructure_hook(Sha1Sum, lambda value: value.hexdigest.lower())

        return converter

    def __init__(
            self,
            *, regex_flags: int | re.RegexFlag = 0,
            detailed_validation: bool = True,
            forbid_extra_keys: bool = False
    ) -> None:
        """
        A converter for converting between structured and unstructured data
        according to the data structures defined in this package.

        Args:
            regex_flags (int | re.RegexFlag, optional):
                Regular expression flags to use when structuring regex pattern from string.
            detailed_validation (bool, optional):
                Whether to use a slightly slower mode for detailed validation errors.
            forbid_extra_keys (bool, optional):
                Raise an error when unknown keys appeared. It has no effect in unstructuring.
                Can be used for test purposes.
        """
        super().__init__(
                unstruct_collection_overrides={
                    collections.abc.Set: list,
                    collections.Counter: dict
                },
                detailed_validation=detailed_validation,
                forbid_extra_keys=forbid_extra_keys,
                omit_if_default=True
        )

        self.configure(self, regex_flags=regex_flags)


@deprecated(
        'createConverter() is now deprecated and will be removed in future versions. '  # noqa
        'Use the class DedicatedConverter to instead.'
)
def createConverter(
        *, detailed_validation: bool = True,
        converter_class: cattrs.Converter | None = None,  # noqa
        regex_flags: int | re.RegexFlag = 0,
) -> 'DedicatedConverter':
    """
    Create and return a dedicated ``cattrs`` converter instance.

    Keyword Args:
        detailed_validation (bool, optional):
            Whether to use a slightly slower mode for detailed validation errors.
        regex_flags (int | re.RegexFlag, optional):
            Regular expression flags to use when structuring regex pattern from string.
        converter_class (cattrs.Converter | None, optional):
            The converter class to use when defining converter.
            **Deprecated**, but retained for backward compatibility purposes.

    **Changed in version 0.3.0:**

    This function is now deprecated and may be removed
    in future versions. You should use the class ``DedicatedConverter`` to instead.

    Now this function will always return a ``mcschemes.tools.parser.converters.DedicatedConverter``
    instance; the kw-only argument ``converter_class`` is no longer determines the type of
    the returned dedicated converter instance.
    """

    return DedicatedConverter(regex_flags=regex_flags, detailed_validation=detailed_validation)
