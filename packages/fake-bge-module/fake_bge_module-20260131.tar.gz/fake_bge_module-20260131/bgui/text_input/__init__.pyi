import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import bgui.widget

class TextInput(bgui.widget.Widget):
    """Widget for getting text input"""

    children: typing.Any
    on_active: typing.Any
    on_click: typing.Any
    on_enter_key: typing.Any
    on_hover: typing.Any
    on_mouse_enter: typing.Any
    on_mouse_exit: typing.Any
    on_release: typing.Any
    parent: typing.Any
    position: typing.Any
    prefix: typing.Any
    size: typing.Any
    system: typing.Any
    text: typing.Any
    theme_options: typing.Any
    theme_section: typing.Any

    def activate(self) -> None: ...
    def calc_mouse_cursor(self, pos) -> None:
        """

        :param pos:
        """

    def deactivate(self) -> None: ...
    def find_mouse_slice(self, pos) -> None:
        """

        :param pos:
        """

    def select_all(self) -> None:
        """Change the selection to include all of the text"""

    def select_none(self) -> None:
        """Change the selection to include none of the text"""

    def swapcolors(self, state=0) -> None:
        """

        :param state:
        """

    def update_selection(self) -> None: ...
