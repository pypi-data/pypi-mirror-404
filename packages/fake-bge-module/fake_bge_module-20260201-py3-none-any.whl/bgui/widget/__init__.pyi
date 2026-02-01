import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

class Animation:
    def update(self) -> None: ...

class WeakMethod: ...

class Widget:
    """The base widget class"""

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

    def add_animation(self, animation) -> None:
        """Add the animation to the list of currently running animations

        :param animation: The animation
        """

    def move(self, position, time, callback=None) -> None:
        """Move a widget to a new position over a number of frames

        :param position:
        :param time: The time in milliseconds to take doing the move
        :param callback: An optional callback that is called when he animation is complete
        """

class ArrayAnimation(Animation):
    def update(self) -> None: ...
