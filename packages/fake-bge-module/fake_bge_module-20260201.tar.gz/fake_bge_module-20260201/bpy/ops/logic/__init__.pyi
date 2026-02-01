import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import bpy.stub_internal.rna_enums
import bpy.types

def actuator_add(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    type: str | None = "",
    name: str = "",
    object: str = "",
) -> None:
    """Add an actuator to the active object

    :param type: Type, Type of actuator to add
    :param name: Name, Name of the Actuator to add
    :param object: Object, Name of the Object to add the Actuator to
    """

def actuator_move(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    actuator: str = "",
    object: str = "",
    direction: typing.Literal["UP", "DOWN"] | None = "UP",
) -> None:
    """Move Actuator

    :param actuator: Actuator, Name of the actuator to edit
    :param object: Object, Name of the object the actuator belongs to
    :param direction: Direction, Move Up or Down
    """

def actuator_remove(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    actuator: str = "",
    object: str = "",
) -> None:
    """Remove an actuator from the active object

    :param actuator: Actuator, Name of the actuator to edit
    :param object: Object, Name of the object the actuator belongs to
    """

def controller_add(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    type: bpy.stub_internal.rna_enums.ControllerTypeItems | None = "LOGIC_AND",
    name: str = "",
    object: str = "",
) -> None:
    """Add a controller to the active object

    :param type: Type, Type of controller to add
    :param name: Name, Name of the Controller to add
    :param object: Object, Name of the Object to add the Controller to
    """

def controller_move(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    controller: str = "",
    object: str = "",
    direction: typing.Literal["UP", "DOWN"] | None = "UP",
) -> None:
    """Move Controller

    :param controller: Controller, Name of the controller to edit
    :param object: Object, Name of the object the controller belongs to
    :param direction: Direction, Move Up or Down
    """

def controller_remove(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    controller: str = "",
    object: str = "",
) -> None:
    """Remove a controller from the active object

    :param controller: Controller, Name of the controller to edit
    :param object: Object, Name of the object the controller belongs to
    """

def custom_object_create(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    class_name: str = "module.MyObject",
) -> None:
    """Create a KX_GameObject subclass and attach it to the selected object

    :param class_name: MyObject, The class name with module (module.ClassName)
    """

def custom_object_register(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    class_name: str = "module.MyObject",
) -> None:
    """Use a custom KX_GameObject subclass for the selected object

    :param class_name: MyObject, The class name with module (module.ClassName)
    """

def custom_object_reload(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Reload custom object from the source script"""

def custom_object_remove(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Remove this custom class from the object"""

def links_cut(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    path: bpy.types.bpy_prop_collection[bpy.types.OperatorMousePath] | None = None,
    cursor: int | None = 15,
) -> None:
    """Remove logic brick connections

    :param path: Path
    :param cursor: Cursor
    """

def properties(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Toggle the properties region visibility"""

def python_component_create(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    component_name: str = "module.Component",
) -> None:
    """Create a Python component to the selected object

    :param component_name: Component, The component class name with module (module.ComponentName)
    """

def python_component_move_down(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Move this component down in the list

    :param index: Index, Component index to move
    """

def python_component_move_up(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Move this component up in the list

    :param index: Index, Component index to move
    """

def python_component_register(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    component_name: str = "module.Component",
) -> None:
    """Add a Python component to the selected object

    :param component_name: Component, The component class name with module (module.ComponentName)
    """

def python_component_reload(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Reload component from the source script

    :param index: Index, Component index to reload
    """

def python_component_remove(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Remove this component from the object

    :param index: Index, Component index to remove
    """

def region_flip(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Toggle the properties regions alignment (left/right)"""

def sensor_add(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    type: str | None = "",
    name: str = "",
    object: str = "",
) -> None:
    """Add a sensor to the active object

    :param type: Type, Type of sensor to add
    :param name: Name, Name of the Sensor to add
    :param object: Object, Name of the Object to add the Sensor to
    """

def sensor_move(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    sensor: str = "",
    object: str = "",
    direction: typing.Literal["UP", "DOWN"] | None = "UP",
) -> None:
    """Move Sensor

    :param sensor: Sensor, Name of the sensor to edit
    :param object: Object, Name of the object the sensor belongs to
    :param direction: Direction, Move Up or Down
    """

def sensor_remove(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    sensor: str = "",
    object: str = "",
) -> None:
    """Remove a sensor from the active object

    :param sensor: Sensor, Name of the sensor to edit
    :param object: Object, Name of the object the sensor belongs to
    """

def view_all(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Resize view so you can see all logic bricks"""
