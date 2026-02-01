import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

def add_game_prop(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Adds a property available to the UPBGE"""

def move_game_prop(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
    direction: str = "",
) -> None:
    """Move Game Property

    :param index: index
    :param direction: direction
    """

def remove_game_prop(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Remove this property

    :param index: index
    """
