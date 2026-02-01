import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import bgui.label
import bgui.widget

class ListBox(bgui.widget.Widget):
    """Widget for displaying a list of data"""

    children: typing.Any
    items: typing.Any
    on_active: typing.Any
    on_click: typing.Any
    on_hover: typing.Any
    on_mouse_enter: typing.Any
    on_mouse_exit: typing.Any
    on_release: typing.Any
    parent: typing.Any
    position: typing.Any
    size: typing.Any
    system: typing.Any
    theme_options: typing.Any
    theme_section: typing.Any

class ListBoxRenderer:
    """Base class for rendering an item in a ListBox"""

    def render_item(self, item) -> bgui.label.Label:
        """Creates and returns a `bgui.label.Label` representation of the supplied item

        :param item: the item to be rendered
        :return:
        """
