import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

def convert_bricks(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Convert Bricks to Nodes"""

def duplicate_brick(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Duplicate this brick"""

def remove_actuator(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    target_brick: str = "",
) -> None:
    """Remove the selected actuator from the selected object

    :param target_brick: target_brick
    """

def remove_controller(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    target_brick: str = "",
) -> None:
    """Remove the selected controller from the selected object

    :param target_brick: target_brick
    """

def remove_sensor(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    target_brick: str = "",
) -> None:
    """Remove the selected sensor from the selected object

    :param target_brick: target_brick
    """

def update_all(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Synchronize logic bricks with the node setup. This should normally happen automatically"""
