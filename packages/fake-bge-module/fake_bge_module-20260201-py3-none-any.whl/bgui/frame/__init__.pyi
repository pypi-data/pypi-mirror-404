import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import bgui.widget

class Frame(bgui.widget.Widget):
    """Frame for storing other widgets"""

    children: typing.Any
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
