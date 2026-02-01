import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import bgui.widget

class System(bgui.widget.Widget):
    """The main gui system. Add widgets to this and then call the render() method
    draw the gui.
    """

    children: typing.Any
    focused_widget: typing.Any
    normalize_text: typing.Any
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

    def render(self) -> None:
        """Renders the GUI system

        :return:
        """

    def update_keyboard(self, key, is_shifted) -> None:
        """Updates the systems keyboard data

        :param key: the key being input
        :param is_shifted: is the shift key held down?
        :return:
        """

    def update_mouse(self, pos, click_state=0) -> None:
        """Updates the systems mouse data

        :param pos: the mouse position
        :param click_state: the current state of the mouse
        :return:
        """
