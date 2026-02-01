import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

class NewSectionProxy:
    """A proxy for a single section from a parser."""

    name: typing.Any
    parser: typing.Any

class Theme:
    """ConfigParser implementing interpolation."""

    BOOLEAN_STATES: typing.Any
    NONSPACECRE: typing.Any
    OPTCRE: typing.Any
    OPTCRE_NV: typing.Any
    SECTCRE: typing.Any
    converters: typing.Any
    path: typing.Any

    def supports(self, widget) -> None:
        """Checks to see if the theme supports a given widget.

        :param widget: the widget to check for support
        """

    def warn_legacy(self, section) -> None:
        """

        :param section:
        """

    def warn_support(self, section) -> None:
        """

        :param section:
        """
