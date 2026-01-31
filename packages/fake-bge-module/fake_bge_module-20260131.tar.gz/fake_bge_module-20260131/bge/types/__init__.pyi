"""
Example:

```
void main()
{
  fragColor = texture(bgl_RenderedTexture, bgl_TexCoord.xy) * vec4(0.0, 0.0, 1.0, 1.0); // will make the rendered image blueish
}
```

Example using offsets:

```
for (int i = 0; i < 9; i++) {
  vec2 offset = g_data.coo_offset[i].xy;
  vec4 sample = texture(bgl_RenderedTexture, bgl_TexCoord.xy + offset);
  // ...
}
```

[QUOTE]
Deprecated since upbge 0.44.


--------------------

This module contains the classes that appear as instances in the Game Engine. A
script must interact with these classes if it is to affect the behaviour of
objects in a game.

The following example would move an object (i.e. an instance of
~bge.types.KX_GameObject) one unit up.

```
# bge.types.SCA_PythonController
cont = bge.logic.getCurrentController()

# bge.types.KX_GameObject
obj = cont.owner
obj.worldPosition.z += 1
```

To run the code, it could be placed in a Blender text block and executed with
a ~bge.types.SCA_PythonController logic brick.


--------------------

bge.types.*

:glob:

"""

import typing
import collections.abc
import typing_extensions
import numpy.typing as npt
import aud
import bpy.types
import mathutils

class BL_ArmatureBone:
    """Proxy to Blender bone structure. All fields are read-only and comply to RNA names.
    All space attribute correspond to the rest pose.
    """

    name: str
    """ bone name."""

    connected: bool
    """ true when the bone head is struck to the parent's tail."""

    hinge: bool
    """ true when bone doesn't inherit rotation or scale from parent bone."""

    inherit_scale: bool
    """ true when bone inherits scaling from parent bone."""

    bbone_segments: int
    """ number of B-bone segments."""

    roll: float
    """ bone rotation around head-tail axis."""

    head: typing.Any
    """ location of head end of the bone in parent bone space."""

    tail: typing.Any
    """ location of head end of the bone in parent bone space."""

    length: float
    """ bone length."""

    arm_head: typing.Any
    """ location of head end of the bone in armature space."""

    arm_tail: typing.Any
    """ location of tail end of the bone in armature space."""

    arm_mat: typing.Any
    """ matrix of the bone head in armature space."""

    bone_mat: typing.Any
    """ rotation matrix of the bone in parent bone space."""

    parent: typing.Any
    """ parent bone, or None for root bone."""

    children: typing.Any
    """ list of bone's children."""

class BL_ArmatureChannel:
    """Proxy to armature pose channel. Allows to read and set armature pose.
    The attributes are identical to RNA attributes, but mostly in read-only mode.
    """

    name: str
    """ channel name (=bone name), read-only."""

    bone: typing.Any
    """ return the bone object corresponding to this pose channel, read-only."""

    parent: typing.Any
    """ return the parent channel object, None if root channel, read-only."""

    has_ik: bool
    """ true if the bone is part of an active IK chain, read-only.
This flag is not set when an IK constraint is defined but not enabled (miss target information for example)."""

    ik_dof_x: bool
    """ true if the bone is free to rotation in the X axis, read-only."""

    ik_dof_y: bool
    """ true if the bone is free to rotation in the Y axis, read-only."""

    ik_dof_z: bool
    """ true if the bone is free to rotation in the Z axis, read-only."""

    ik_limit_x: bool
    """ true if a limit is imposed on X rotation, read-only."""

    ik_limit_y: bool
    """ true if a limit is imposed on Y rotation, read-only."""

    ik_limit_z: bool
    """ true if a limit is imposed on Z rotation, read-only."""

    ik_rot_control: bool
    """ true if channel rotation should applied as IK constraint, read-only."""

    ik_lin_control: bool
    """ true if channel size should applied as IK constraint, read-only."""

    location: typing.Any
    """ displacement of the bone head in armature local space, read-write."""

    scale: typing.Any
    """ scale of the bone relative to its parent, read-write."""

    rotation_quaternion: typing.Any
    """ rotation of the bone relative to its parent expressed as a quaternion, read-write."""

    rotation_euler: typing.Any
    """ rotation of the bone relative to its parent expressed as a set of euler angles, read-write."""

    rotation_mode: typing.Any
    """ Method of updating the bone rotation, read-write."""

    channel_matrix: typing.Any
    """ pose matrix in bone space (deformation of the bone due to action, constraint, etc), Read-only.
This field is updated after the graphic render, it represents the current pose."""

    pose_matrix: typing.Any
    """ pose matrix in armature space, read-only,
This field is updated after the graphic render, it represents the current pose."""

    pose_head: typing.Any
    """ position of bone head in armature space, read-only."""

    pose_tail: typing.Any
    """ position of bone tail in armature space, read-only."""

    ik_min_x: float
    """ minimum value of X rotation in degree (<= 0) when X rotation is limited (see ik_limit_x), read-only."""

    ik_max_x: float
    """ maximum value of X rotation in degree (>= 0) when X rotation is limited (see ik_limit_x), read-only."""

    ik_min_y: float
    """ minimum value of Y rotation in degree (<= 0) when Y rotation is limited (see ik_limit_y), read-only."""

    ik_max_y: float
    """ maximum value of Y rotation in degree (>= 0) when Y rotation is limited (see ik_limit_y), read-only."""

    ik_min_z: float
    """ minimum value of Z rotation in degree (<= 0) when Z rotation is limited (see ik_limit_z), read-only."""

    ik_max_z: float
    """ maximum value of Z rotation in degree (>= 0) when Z rotation is limited (see ik_limit_z), read-only."""

    ik_stiffness_x: typing.Any
    """ bone rotation stiffness in X axis, read-only."""

    ik_stiffness_y: typing.Any
    """ bone rotation stiffness in Y axis, read-only."""

    ik_stiffness_z: typing.Any
    """ bone rotation stiffness in Z axis, read-only."""

    ik_stretch: float
    """ ratio of scale change that is allowed, 0=bone can't change size, read-only."""

    ik_rot_weight: typing.Any
    """ weight of rotation constraint when ik_rot_control is set, read-write."""

    ik_lin_weight: typing.Any
    """ weight of size constraint when ik_lin_control is set, read-write."""

    joint_rotation: typing.Any
    """ Control bone rotation in term of joint angle (for robotic applications), read-write.When writing to this attribute, you pass a [x, y, z] vector and an appropriate set of euler angles or quaternion is calculated according to the rotation_mode.When you read this attribute, the current pose matrix is converted into a [x, y, z] vector representing the joint angles.The value and the meaning of the x, y, z depends on the ik_dof_x/ik_dof_y/ik_dof_z attributes:"""

class BL_ArmatureConstraint:
    """Proxy to Armature Constraint. Allows to change constraint on the fly.
    Obtained through `~bge.types.BL_ArmatureObject`.constraints.
    """

    type: int
    """ Type of constraint, (read-only).Use one of `these constants<armatureconstraint-constants-type>`."""

    name: str
    """ Name of constraint constructed as <bone_name>:<constraint_name>. constraints list.This name is also the key subscript on `~bge.types.BL_ArmatureObject`."""

    enforce: float
    """ fraction of constraint effect that is enforced. Between 0 and 1."""

    headtail: typing.Any
    """ Position of target between head and tail of the target bone: 0=head, 1=tail."""

    lin_error: float
    """ runtime linear error (in Blender units) on constraint at the current frame.This is a runtime value updated on each frame by the IK solver. Only available on IK constraint and iTaSC solver."""

    rot_error: typing.Any
    """ Runtime rotation error (in radiant) on constraint at the current frame.This is a runtime value updated on each frame by the IK solver. Only available on IK constraint and iTaSC solver.It is only set if the constraint has a rotation part, for example, a CopyPose+Rotation IK constraint."""

    target: typing.Any
    """ Primary target object for the constraint. The position of this object in the GE will be used as target for the constraint."""

    subtarget: typing.Any
    """ Secondary target object for the constraint. The position of this object in the GE will be used as secondary target for the constraint.Currently this is only used for pole target on IK constraint."""

    active: bool
    """ True if the constraint is active."""

    ik_weight: float
    """ Weight of the IK constraint between 0 and 1.Only defined for IK constraint."""

    ik_type: int
    """ Type of IK constraint, (read-only).Use one of `these constants<armatureconstraint-constants-ik-type>`."""

    ik_flag: int
    """ Combination of IK constraint option flags, read-only.Use one of `these constants<armatureconstraint-constants-ik-flag>`."""

    ik_dist: float
    """ Distance the constraint is trying to maintain with target, only used when ik_type=CONSTRAINT_IK_DISTANCE."""

    ik_mode: int
    """ Use one of `these constants<armatureconstraint-constants-ik-mode>`.Additional mode for IK constraint. Currently only used for Distance constraint:"""

class BL_ArmatureObject:
    """An armature object."""

    constraints: typing.Any
    """ The list of armature constraint defined on this armature.
Elements of the list can be accessed by index or string.
The key format for string access is '<bone_name>:<constraint_name>'."""

    channels: typing.Any
    """ The list of armature channels.
Elements of the list can be accessed by index or name the bone."""

    def update(self) -> None:
        """Ensures that the armature will be updated on next graphic frame.This action is unnecessary if a KX_ArmatureActuator with mode run is active
        or if an action is playing. Use this function in other cases. It must be called
        on each frame to ensure that the armature is updated continuously.

        """

    def draw(self) -> None:
        """Draw lines that represent armature to view it in real time."""

class BL_Shader:
    """BL_Shader is a class used to compile and use custom shaders scripts.
    This header set the #version directive, so the user must not define his own #version.
    Since 0.3.0, this class is only used with custom 2D filters.The list of python callbacks executed when the shader is used to render an object.
    All the functions can expect as argument the object currently rendered.def callback(object):
        print("render object %r" % object.name)type

    list of functions and/or methods0.3.0The list of python callbacks executed when the shader is begin used to render.type

    list of functions and/or methods0.3.0Clear the shader. Use this method before the source is changed with `setSource`.0.3.0Set attribute location. (The parameter is ignored a.t.m. and the value of "tangent" is always used.)arg enum

    attribute location value

    type enum

    integer0.3.0Set the vertex and fragment programsarg vertexProgram

    Vertex program

    type vertexProgram

    string

    arg fragmentProgram

    Fragment program

    type fragmentProgram

    string

    arg apply

    Enable the shader.

    type apply

    boolean0.3.0Set the vertex, fragment and geometry shader programs.arg sources

    Dictionary of all programs. The keys `vertex`, `fragment` and `geometry` represent shader programs of the same name.
    `geometry` is an optional program.
    This dictionary can be similar to:

    sources = {
        "vertex" : vertexProgram,
        "fragment" : fragmentProgram,
        "geometry" : geometryProgram
    }

    type sources

    dict

    arg apply

    Enable the shader.

    type apply

    boolean0.3.0Set a uniform with a float value that reflects the eye being render in stereo mode:
    0.0 for the left eye, 0.5 for the right eye. In non stereo mode, the value of the uniform
    is fixed to 0.0. The typical use of this uniform is in stereo mode to sample stereo textures
    containing the left and right eye images in a top-bottom order.arg name

    the uniform name

    type name

    string0.3.0
    """

    enabled: bool
    """ Set shader enabled to use."""

    objectCallbacks: typing.Any
    bindCallbacks: typing.Any

    def setUniformfv(self, name: str, fList: list[float]) -> None:
        """Set a uniform with a list of float values

        :param name: the uniform name
        :param fList: a list (2, 3 or 4 elements) of float values
        """

    def delSource(self) -> None: ...
    def getFragmentProg(self) -> str:
        """Returns the fragment program.

        :return: The fragment program.
        """

    def getVertexProg(self) -> str:
        """Get the vertex program.

        :return: The vertex program.
        """

    def isValid(self) -> bool:
        """Check if the shader is valid.

        :return: True if the shader is valid
        """

    def setAttrib(self, enum) -> None:
        """

        :param enum:
        """

    def setSampler(self, name: str, index: int) -> None:
        """Set uniform texture sample index.

        :param name: Uniform name
        :param index: Texture sample index.
        """

    def setSource(self, vertexProgram, fragmentProgram, apply) -> None:
        """

        :param vertexProgram:
        :param fragmentProgram:
        :param apply:
        """

    def setSourceList(self, sources, apply) -> None:
        """

        :param sources:
        :param apply:
        """

    def setUniform1f(self, name: str, fx: float) -> None:
        """Set a uniform with 1 float value.

        :param name: the uniform name
        :param fx: Uniform value
        """

    def setUniform1i(self, name: str, ix: int) -> None:
        """Set a uniform with an integer value.

        :param name: the uniform name
        :param ix: the uniform value
        """

    def setUniform2f(self, name: str, fx: float, fy: float) -> None:
        """Set a uniform with 2 float values

        :param name: the uniform name
        :param fx: first float value
        :param fy: second float value
        """

    def setUniform2i(self, name: str, ix: int, iy: int) -> None:
        """Set a uniform with 2 integer values

        :param name: the uniform name
        :param ix: first integer value
        :param iy: second integer value
        """

    def setUniform3f(self, name: str, fx: float, fy: float, fz: float) -> None:
        """Set a uniform with 3 float values.

        :param name: the uniform name
        :param fx: first float value
        :param fy: second float value
        :param fz: third float value
        """

    def setUniform3i(self, name: str, ix: int, iy: int, iz: int) -> None:
        """Set a uniform with 3 integer values

        :param name: the uniform name
        :param ix: first integer value
        :param iy: second integer value
        :param iz: third integer value
        """

    def setUniform4f(
        self, name: str, fx: float, fy: float, fz: float, fw: float
    ) -> None:
        """Set a uniform with 4 float values.

        :param name: the uniform name
        :param fx: first float value
        :param fy: second float value
        :param fz: third float value
        :param fw: fourth float value
        """

    def setUniform4i(self, name: str, ix: int, iy: int, iz: int, iw: int) -> None:
        """Set a uniform with 4 integer values

        :param name: the uniform name
        :param ix: first integer value
        :param iy: second integer value
        :param iz: third integer value
        :param iw: fourth integer value
        """

    def setUniformDef(self, name: str, type: int) -> None:
        """Define a new uniform

        :param name: the uniform name
        :param type: uniform type, one of `these constants <shader-defined-uniform>`
        """

    def setUniformMatrix3(self, name: str, mat, transpose: bool) -> None:
        """Set a uniform with a 3x3 matrix value

        :param name: the uniform name
        :param mat: A 3x3 matrix [[f, f, f], [f, f, f], [f, f, f]]
        :param transpose: set to True to transpose the matrix
        """

    def setUniformMatrix4(self, name: str, mat, transpose: bool) -> None:
        """Set a uniform with a 4x4 matrix value

        :param name: the uniform name
        :param mat: A 4x4 matrix [[f, f, f, f], [f, f, f, f], [f, f, f, f], [f, f, f, f]]
        :param transpose: set to True to transpose the matrix
        """

    def setUniformiv(self, name: str, iList: list[int]) -> None:
        """Set a uniform with a list of integer values

        :param name: the uniform name
        :param iList: a list (2, 3 or 4 elements) of integer values
        """

    def setUniformEyef(self, name) -> None:
        """

        :param name:
        """

    def validate(self) -> None:
        """Validate the shader object."""

class EXP_Value:
    """This class is a basis for other classes."""

    name: str
    """ The name of this EXP_Value derived object (read-only)."""

class EXP_ListValue:
    """This is a list like object used in the game engine internally that behaves similar to a python list in most ways.As well as the normal index lookup (val= clist[i]), EXP_ListValue supports string lookups (val= scene.objects["Cube"])Other operations such as len(clist), list(clist), clist[0:10] are also supported."""

    def append(self, val) -> None:
        """Add an item to the list (like pythons append)

        :param val:
        """

    def count(self, val) -> int:
        """Count the number of instances of a value in the list.

        :param val:
        :return: number of instances
        """

    def index(self, val) -> int:
        """Return the index of a value in the list.

        :param val:
        :return: The index of the value in the list.
        """

    def reverse(self) -> None:
        """Reverse the order of the list."""

    def get(self, key, default=None) -> None:
        """Return the value matching key, or the default value if its not found.

        :param key:
        :param default:
        :return: The key value or a default.
        """

    def filter(self, name, prop) -> None:
        """Return a list of items with name matching name regex and with a property matching prop regex.
        If name is empty every items are checked, if prop is empty no property check is proceeded.

                :param name:
                :param prop:
                :return: The list of matching items.
        """

    def from_id(self, id) -> None:
        """This is a function especially for the game engine to return a value with a specific id.Since object names are not always unique, the id of an object can be used to get an object from the CValueList.Example:Where myObID is an int or long from the id function.This has the advantage that you can store the id in places you could not store a gameObject.

        :param id:
        """

class EXP_PropValue:
    """This class has no python functions"""

class EXP_PyObjectPlus:
    """EXP_PyObjectPlus base class of most other types in the Game Engine."""

    invalid: bool
    """ Test if the object has been freed by the game engine and is no longer valid.Normally this is not a problem but when storing game engine data in the GameLogic module,
KX_Scenes or other KX_GameObjects its possible to hold a reference to invalid data.
Calling an attribute or method on an invalid object will raise a SystemError.The invalid attribute allows testing for this case without exception handling."""

class KX_2DFilter:
    """2D filter shader object. Can be alternated with `~bge.types.BL_Shader`s functions."""

class KX_2DFilterFrameBuffer:
    """2D filter custom off screen (framebuffer in 0.3+)."""

    width: int
    """ The off screen width, always canvas width in 0.3+ (read-only)."""

    height: int
    """ The off screen height, always canvas height in 0.3+ (read-only)."""

    def getColorTexture(self) -> None:
        """Returns the buffer color texture.

        :return: Texture object.
        """

    def getDepthTexture(self) -> None:
        """Returns the buffer depth texture.

        :return: Texture object.
        """

class KX_2DFilterManager:
    """2D filter manager used to add, remove and find filters in a scene."""

    def addFilter(
        self, index: int, type: int, fragmentProgram: str | None = ""
    ) -> None:
        """Add a filter to the pass index `index`, type `type` and fragment program if custom filter.

                :param index: The filter pass index.
                :param type: The filter type, one of:

        `bge.logic.RAS_2DFILTER_BLUR`

        `bge.logic.RAS_2DFILTER_DILATION`

        `bge.logic.RAS_2DFILTER_EROSION`

        `bge.logic.RAS_2DFILTER_SHARPEN`

        `bge.logic.RAS_2DFILTER_LAPLACIAN`

        `bge.logic.RAS_2DFILTER_PREWITT`

        `bge.logic.RAS_2DFILTER_SOBEL`

        `bge.logic.RAS_2DFILTER_GRAYSCALE`

        `bge.logic.RAS_2DFILTER_SEPIA`

        `bge.logic.RAS_2DFILTER_CUSTOMFILTER`
                :param fragmentProgram: The filter shader fragment program.
        Specified only if `type` is `bge.logic.RAS_2DFILTER_CUSTOMFILTER`. (optional)
                :return: The 2D Filter.
        """

    def removeFilter(self, index: int) -> None:
        """Remove filter to the pass index `index`.

        :param index: The filter pass index.
        """

    def getFilter(self, index: int) -> None:
        """Return filter to the pass index `index`.

        :param index: The filter pass index.
        :return: The filter in the specified pass index or None.
        """

class KX_BlenderMaterial:
    """This is kept for backward compatibility with some scripts."""

    textures: typing.Any
    """ List of all material's textures (read only)."""

class KX_Camera:
    """A Camera object."""

    INSIDE: typing.Any
    """ See `sphereInsideFrustum` and `boxInsideFrustum`"""

    INTERSECT: typing.Any
    """ See `sphereInsideFrustum` and `boxInsideFrustum`"""

    OUTSIDE: typing.Any
    """ See `sphereInsideFrustum` and `boxInsideFrustum`"""

    lens: float
    """ The camera's lens value."""

    lodDistanceFactor: float
    """ The factor to multiply distance to camera to adjust levels of detail.
A float < 1.0f will make the distance to camera used to compute
levels of detail decrease."""

    fov: float
    """ The camera's field of view value."""

    ortho_scale: float
    """ The camera's view scale when in orthographic mode."""

    near: float
    """ The camera's near clip distance."""

    far: float
    """ The camera's far clip distance."""

    shift_x: float
    """ The camera's horizontal shift."""

    shift_y: float
    """ The camera's vertical shift."""

    perspective: bool
    """ True if this camera has a perspective transform, False for an orthographic projection."""

    projection_matrix: typing.Any
    """ This camera's 4x4 projection matrix."""

    modelview_matrix: typing.Any
    """ This camera's 4x4 model view matrix. (read-only)."""

    camera_to_world: typing.Any
    """ This camera's camera to world transform. (read-only)."""

    world_to_camera: typing.Any
    """ This camera's world to camera transform. (read-only)."""

    useViewport: bool
    """ True when the camera is used as a viewport, set True to enable a viewport for this camera."""

    activityCulling: bool
    """ True if this camera is used to compute object distance for object activity culling."""

    def sphereInsideFrustum(self, centre, radius: float) -> int:
        """Tests the given sphere against the view frustum.

        :param centre: The centre of the sphere (in world coordinates.)
        :param radius: the radius of the sphere
        :return: `~bge.types.KX_Camera.INSIDE`, `~bge.types.KX_Camera.OUTSIDE` or `~bge.types.KX_Camera.INTERSECT`
        """

    def boxInsideFrustum(self, box) -> None:
        """Tests the given box against the view frustum.

        :param box: Eight (8) corner points of the box (in world coordinates.)
        :return: `~bge.types.KX_Camera.INSIDE`, `~bge.types.KX_Camera.OUTSIDE` or `~bge.types.KX_Camera.INTERSECT`
        """

    def pointInsideFrustum(
        self, point: collections.abc.Sequence[float] | mathutils.Vector
    ) -> bool:
        """Tests the given point against the view frustum.

        :param point: The point to test (in world coordinates.)
        :return: True if the given point is inside this cameras viewing frustum.
        """

    def getCameraToWorld(self) -> None:
        """Returns the camera-to-world transform.

        :return: the camera-to-world transform matrix.
        """

    def getWorldToCamera(self) -> None:
        """Returns the world-to-camera transform.This returns the inverse matrix of getCameraToWorld().

        :return: the world-to-camera transform matrix.
        """

    def setOnTop(self) -> None:
        """Set this cameras viewport ontop of all other viewport."""

    def setViewport(self, left: int, bottom: int, right: int, top: int) -> None:
        """Sets the region of this viewport on the screen in pixels.Use `bge.render.getWindowHeight` and `bge.render.getWindowWidth` to calculate values relative to the entire display.

        :param left: left pixel coordinate of this viewport
        :param bottom: bottom pixel coordinate of this viewport
        :param right: right pixel coordinate of this viewport
        :param top: top pixel coordinate of this viewport
        """

    def getScreenPosition(
        self, object: collections.abc.Sequence[float] | mathutils.Vector
    ) -> None:
        """Gets the position of an object projected on screen space.

        :param object: object name or list [x, y, z]
        :return: the objects position in screen coordinates.
        """

    def getScreenVect(
        self, x: float, y: float
    ) -> collections.abc.Sequence[float] | mathutils.Vector:
        """Gets the vector from the camera position in the screen coordinate direction.

        :param x: X Axis
        :param y: Y Axis
        :return: The vector from screen coordinate.
        """

    def getScreenRay(
        self, x: float, y: float, dist: float = inf, property: str | None = None
    ) -> None:
        """Look towards a screen coordinate (x, y) and find first object hit within dist that matches prop.
        The ray is similar to KX_GameObject->rayCastTo.

                :param x: X Axis
                :param y: Y Axis
                :param dist: max distance to look (can be negative => look behind); 0 or omitted => detect up to other
                :param property: property name that object must have; can be omitted => detect any object
                :return: the first object hit or None if no object or object does not match prop
        """

class KX_CharacterWrapper:
    """A wrapper to expose character physics options."""

    onGround: bool
    """ Whether or not the character is on the ground. (read-only)"""

    gravity: typing.Any
    """ The gravity vector used for the character."""

    fallSpeed: float
    """ The character falling speed."""

    maxJumps: int
    """ The maximum number of jumps a character can perform before having to touch the ground. By default this is set to 1. 2 allows for a double jump, etc."""

    jumpCount: int
    """ The current jump count. This can be used to have different logic for a single jump versus a double jump. For example, a different animation for the second jump."""

    jumpSpeed: float
    """ The character jumping speed."""

    maxSlope: float
    """ The maximum slope which the character can climb."""

    walkDirection: typing.Any
    """ The speed and direction the character is traveling in using world coordinates. This should be used instead of applyMovement() to properly move the character."""

    def jump(self) -> None:
        """The character jumps based on its jump speed."""

    def setVelocity(
        self,
        velocity: collections.abc.Sequence[float] | mathutils.Vector,
        time: float,
        local: bool = False,
    ) -> None:
        """Sets the characters linear velocity for a given period.This method sets characters velocity through its center of mass during a period.

                :param velocity: Linear velocity vector.
                :param time: Period while applying linear velocity.
                :param local: False: you get the "global" velocity ie: relative to world orientation.

        True: you get the "local" velocity ie: relative to object orientation.
        """

    def reset(self) -> None:
        """Resets the character velocity and walk direction."""

class KX_CollisionContactPoint:
    """A collision contact point passed to the collision callbacks."""

    localPointA: mathutils.Vector
    """ The contact point in the owner object space."""

    localPointB: mathutils.Vector
    """ The contact point in the collider object space."""

    worldPoint: mathutils.Vector
    """ The contact point in world space."""

    normal: mathutils.Vector
    """ The contact normal in owner object space."""

    combinedFriction: float
    """ The combined friction of the owner and collider object."""

    combinedRollingFriction: float
    """ The combined rolling friction of the owner and collider object."""

    combinedRestitution: float
    """ The combined restitution of the owner and collider object."""

    appliedImpulse: float
    """ The applied impulse to the owner object."""

class KX_ConstraintWrapper:
    """KX_ConstraintWrapper"""

    constraint_id: int
    """ Returns the constraint ID  (read only)"""

    constraint_type: int
    """ Returns the constraint type (read only)"""

    breakingThreshold: typing.Any
    """ The impulse threshold breaking the constraint, if the constraint is broken `enabled` is set to False."""

    enabled: bool
    """ The status of the constraint. Set to True to restore a constraint after breaking."""

    def getConstraintId(self, val) -> int:
        """Returns the constraint ID

        :param val:
        :return: the constraint ID
        """

    def setParam(self, axis: int, value0: float, value1: float) -> None:
        """Set the constraint limitsFor PHY_LINEHINGE_CONSTRAINT = 2 or PHY_ANGULAR_CONSTRAINT = 3:For PHY_CONE_TWIST_CONSTRAINT = 4:For PHY_GENERIC_6DOF_CONSTRAINT = 12:

        :param axis:
        :param value0: Set the minimum limit of the axisSet the minimum limit of the axisSet the minimum limit of the axisSet the linear velocity of the axisSet the stiffness of the spring
        :param value1: Set the maximum limit of the axisSet the maximum limit of the axisSet the maximum limit of the axisSet the maximum force limit of the axisTendency of the spring to return to its original position
        """

    def getParam(self, axis: int) -> float:
        """Get the constraint position or euler angle of a generic 6DOF constraint

        :param axis:
        :return: positionangle
        """

class KX_FontObject:
    """A Font game object.It is possible to use attributes from :type: `~bpy.types.TextCurve`"""

class KX_GameObject:
    """All game objects are derived from this class.Properties assigned to game objects are accessible as attributes of this class.KX_GameObject can be subclassed to extend functionality. For example:When subclassing objects other than empties and meshes, the specific type
    should be used - e.g. inherit from `~bge.types.BL_ArmatureObject` when the object
    to mutate is an armature.The layer mask used for shadow and real-time cube map render.type

    integer (bit mask)0.3.0(You can use bpy.types.Object.bound_box instead) The objects bounding volume box used for culling.type

    `~bge.types.KX_BoundingBox`0.3.0Returns True if the object is culled, else False.This variable returns an invalid value if it is called outside the scenes callbacks `KX_Scene.pre_draw <~bge.types.KX_Scene.pre_draw>` and `KX_Scene.post_draw <~bge.types.KX_Scene.post_draw>`.type

    boolean (read only)0.3.0occlusion capability flag.type

    boolean0.3.0The object batch group containing the batched mesh.type

    `~bge.types.KX_BatchGroup`0.3.0Sets the game objects occlusion capability.arg occlusion

    the state to set the occlusion to.

    type occlusion

    boolean

    arg recursive

    optional argument to set all childrens visibility flag too, defaults to False if no value passed.

    type recursive

    boolean0.3.0Gets the game objects reaction force.The reaction force is the force applied to this object over the last simulation timestep.
    This also includes impulses, eg from collisions.return

    the reaction force of this object.

    rtype

    Vector((fx, fy, fz))This is not implemented at the moment. (Removed when switching from Sumo to Bullet)0.0.0
    """

    name: str
    """ The object's name."""

    mass: float
    """ The object's mass"""

    friction: float
    """ The object's friction"""

    isSuspendDynamics: bool
    """ The object's dynamic state (read-only).:py:meth:`suspendDynamics` and :py:meth:`restoreDynamics` allow you to change the state."""

    linearDamping: typing.Any
    """ The object's linear damping, also known as translational damping. Can be set simultaneously with angular damping using the `setDamping` method."""

    angularDamping: typing.Any
    """ The object's angular damping, also known as rotationation damping. Can be set simultaneously with linear damping using the `setDamping` method."""

    linVelocityMin: float
    """ Enforces the object keeps moving at a minimum velocity."""

    linVelocityMax: float
    """ Clamp the maximum linear velocity to prevent objects moving beyond a set speed."""

    angularVelocityMin: typing.Any
    """ Enforces the object keeps rotating at a minimum velocity. A value of 0.0 disables this."""

    angularVelocityMax: typing.Any
    """ Clamp the maximum angular velocity to prevent objects rotating beyond a set speed.
A value of 0.0 disables clamping; it does not stop rotation."""

    localInertia: typing.Any
    """ the object's inertia vector in local coordinates. Read only."""

    parent: typing.Any
    """ The object's parent object. (read-only)."""

    groupMembers: typing.Any
    """ Returns the list of group members if the object is a group object (dupli group instance), otherwise None is returned."""

    groupObject: typing.Any
    """ Returns the group object (dupli group instance) that the object belongs to or None if the object is not part of a group."""

    collisionGroup: typing.Any
    """ The object's collision group."""

    collisionMask: typing.Any
    """ The object's collision mask."""

    collisionCallbacks: typing.Any
    """ A list of functions to be called when a collision occurs.Callbacks should either accept one argument (object), or four
arguments (object, point, normal, points). For simplicity, per
colliding object the first collision point is reported in second
and third argument."""

    scene: typing.Any
    """ The object's scene. (read-only)."""

    visible: bool
    """ visibility flag."""

    layer: typing.Any
    cullingBox: typing.Any
    culled: typing.Any
    color: mathutils.Vector
    """ The object color of the object. [r, g, b, a]"""

    physicsCulling: bool
    """ True if the object suspends its physics depending on its nearest distance to any camera."""

    logicCulling: bool
    """ True if the object suspends its logic and animation depending on its nearest distance to any camera."""

    physicsCullingRadius: float
    """ Suspend object's physics if this radius is smaller than its nearest distance to any camera
and `physicsCulling` set to True."""

    logicCullingRadius: float
    """ Suspend object's logic and animation if this radius is smaller than its nearest distance to any camera
and `logicCulling` set to True."""

    occlusion: typing.Any
    position: mathutils.Vector
    """ The object's position. [x, y, z] On write: local position, on read: world positionUse `localPosition` and `worldPosition`.0.0.1"""

    orientation: mathutils.Matrix
    """ The object's orientation. 3x3 Matrix. You can also write a Quaternion or Euler vector. On write: local orientation, on read: world orientationUse `localOrientation` and `worldOrientation`.0.0.1"""

    scaling: mathutils.Vector
    """ The object's scaling factor. [sx, sy, sz] On write: local scaling, on read: world scalingUse `localScale` and `worldScale`.0.0.1"""

    localOrientation: mathutils.Matrix
    """ The object's local orientation. 3x3 Matrix. You can also write a Quaternion or Euler vector."""

    worldOrientation: mathutils.Matrix
    """ The object's world orientation. 3x3 Matrix."""

    localScale: mathutils.Vector
    """ The object's local scaling factor. [sx, sy, sz]"""

    worldScale: mathutils.Vector
    """ The object's world scaling factor. [sx, sy, sz]"""

    localPosition: mathutils.Vector
    """ The object's local position. [x, y, z]"""

    worldPosition: mathutils.Vector
    """ The object's world position. [x, y, z]"""

    localTransform: mathutils.Matrix
    """ The object's local space transform matrix. 4x4 Matrix."""

    worldTransform: mathutils.Matrix
    """ The object's world space transform matrix. 4x4 Matrix."""

    localLinearVelocity: mathutils.Vector
    """ The object's local linear velocity. [x, y, z]"""

    worldLinearVelocity: mathutils.Vector
    """ The object's world linear velocity. [x, y, z]"""

    localAngularVelocity: mathutils.Vector
    """ The object's local angular velocity. [x, y, z]"""

    worldAngularVelocity: mathutils.Vector
    """ The object's world angular velocity. [x, y, z]"""

    gravity: mathutils.Vector
    """ The object's gravity. [x, y, z]"""

    timeOffset: float
    """ adjust the slowparent delay at runtime."""

    blenderObject: typing.Any
    """ This KX_GameObject's Object."""

    state: int
    """ the game object's state bitmask, using the first 30 bits, one bit must always be set."""

    meshes: typing.Any
    """ a list meshes for this object."""

    batchGroup: typing.Any
    sensors: list
    """ a sequence of `~bge.types.SCA_ISensor` objects with string/index lookups and iterator support."""

    controllers: typing.Any
    """ a sequence of `~bge.types.SCA_IController` objects with string/index lookups and iterator support."""

    actuators: list
    """ a list of `~bge.types.SCA_IActuator` with string/index lookups and iterator support."""

    attrDict: dict
    """ get the objects internal python attribute dictionary for direct (faster) access."""

    components: typing.Any
    """ All python components."""

    children: typing.Any
    """ direct children of this object, (read-only)."""

    childrenRecursive: typing.Any
    """ all children of this object including children's children, (read-only)."""

    life: float
    """ The number of frames until the object ends, assumes one frame is 1/60 second (read-only)."""

    debug: bool
    """ If true, the object's debug properties will be displayed on screen."""

    debugRecursive: bool
    """ If true, the object's and children's debug properties will be displayed on screen."""

    currentLodLevel: int
    """ The index of the level of detail (LOD) currently used by this object (read-only)."""

    lodManager: typing.Any
    """ Return the lod manager of this object.
Needed to access to lod manager to set attributes of levels of detail of this object.
The lod manager is shared between instance objects and can be changed to use the lod levels of an other object.
If the lod manager is set to None the object's mesh backs to the mesh of the previous first lod level."""

    onRemove: list
    """ A list of callables to run when the KX_GameObject is destroyed.or"""

    logger: typing.Any
    """ A logger instance that can be used to log messages related to this object (read-only)."""

    loggerName: str
    """ A name used to create the logger instance. By default, it takes the form Type[Name]
and can be optionally overridden as below:"""

    def endObject(self) -> None:
        """Delete this object, can be used in place of the EndObject Actuator.The actual removal of the object from the scene is delayed."""

    def replaceMesh(
        self, mesh: str, useDisplayMesh: bool = True, usePhysicsMesh: bool = False
    ) -> None:
        """Replace the mesh of this object with a new mesh. This works the same was as the actuator.

        :param mesh: mesh to replace or the meshes name.
        :param useDisplayMesh: when enabled the display mesh will be replaced (optional argument).
        :param usePhysicsMesh: when enabled the physics mesh will be replaced (optional argument).
        """

    def setVisible(self, visible: bool, recursive: bool | None = False) -> None:
        """Sets the game objects visible flag.

        :param visible: the visible state to set.
        :param recursive: optional argument to set all childrens visibility flag too, defaults to False if no value passed.
        """

    def setOcclusion(self, occlusion, recursive) -> None:
        """

        :param occlusion:
        :param recursive:
        """

    def alignAxisToVect(
        self,
        vect: collections.abc.Sequence[float] | mathutils.Vector,
        axis: int = 2,
        factor: float = 1.0,
    ) -> None:
        """Aligns any of the game objects axis along the given vector.

                :param vect: a vector to align the axis.
                :param axis: The axis you want to align

        0: X axis

        1: Y axis

        2: Z axis
                :param factor: Only rotate a fraction of the distance to the target vector (0.0 - 1.0)
        """

    def getAxisVect(
        self, vect: collections.abc.Sequence[float] | mathutils.Vector
    ) -> None:
        """Returns the axis vector rotates by the objects worldspace orientation.
        This is the equivalent of multiplying the vector by the orientation matrix.

                :param vect: a vector to align the axis.
                :return: The vector in relation to the objects rotation.
        """

    def applyMovement(
        self, movement: collections.abc.Sequence[float] | mathutils.Vector, local
    ) -> None:
        """Sets the game objects movement.

                :param movement: movement vector.
                :param local: False: you get the "global" movement ie: relative to world orientation.

        True: you get the "local" movement ie: relative to object orientation.

        Default to False if not passed.boolean
        """

    def applyRotation(
        self, rotation: collections.abc.Sequence[float] | mathutils.Vector, local
    ) -> None:
        """Sets the game objects rotation.

                :param rotation: rotation vector.
                :param local: False: you get the "global" rotation ie: relative to world orientation.

        True: you get the "local" rotation ie: relative to object orientation.

        Default to False if not passed.boolean
        """

    def applyForce(
        self, force: collections.abc.Sequence[float] | mathutils.Vector, local: bool
    ) -> None:
        """Sets the game objects force.This requires a dynamic object.

                :param force: force vector.
                :param local: False: you get the "global" force ie: relative to world orientation.

        True: you get the "local" force ie: relative to object orientation.

        Default to False if not passed.
        """

    def applyTorque(
        self, torque: collections.abc.Sequence[float] | mathutils.Vector, local: bool
    ) -> None:
        """Sets the game objects torque.This requires a dynamic object.

                :param torque: torque vector.
                :param local: False: you get the "global" torque ie: relative to world orientation.

        True: you get the "local" torque ie: relative to object orientation.

        Default to False if not passed.
        """

    def getLinearVelocity(self, local: bool) -> None:
        """Gets the game objects linear velocity.This method returns the game objects velocity through its center of mass, ie no angular velocity component.

                :param local: False: you get the "global" velocity ie: relative to world orientation.

        True: you get the "local" velocity ie: relative to object orientation.

        Default to False if not passed.
                :return: the objects linear velocity.
        """

    def setLinearVelocity(
        self, velocity: collections.abc.Sequence[float] | mathutils.Vector, local: bool
    ) -> None:
        """Sets the game objects linear velocity.This method sets game objects velocity through its center of mass,
        ie no angular velocity component.This requires a dynamic object.

                :param velocity: linear velocity vector.
                :param local: False: you get the "global" velocity ie: relative to world orientation.

        True: you get the "local" velocity ie: relative to object orientation.

        Default to False if not passed.
        """

    def getAngularVelocity(self, local: bool) -> None:
        """Gets the game objects angular velocity.

                :param local: False: you get the "global" velocity ie: relative to world orientation.

        True: you get the "local" velocity ie: relative to object orientation.

        Default to False if not passed.
                :return: the objects angular velocity.
        """

    def setAngularVelocity(self, velocity: bool, local) -> None:
        """Sets the game objects angular velocity.This requires a dynamic object.

                :param velocity: angular velocity vector.
                :param local: False: you get the "global" velocity ie: relative to world orientation.

        True: you get the "local" velocity ie: relative to object orientation.

        Default to False if not passed.
        """

    def getVelocity(
        self, point: collections.abc.Sequence[float] | mathutils.Vector | None = []
    ) -> None:
        """Gets the game objects velocity at the specified point.Gets the game objects velocity at the specified point, including angular
        components.

                :param point: optional point to return the velocity for, in local coordinates, defaults to (0, 0, 0) if no value passed.
                :return: the velocity at the specified point.
        """

    def getReactionForce(self) -> None: ...
    def applyImpulse(
        self,
        point,
        impulse: collections.abc.Sequence[float] | mathutils.Vector,
        local: bool,
    ) -> None:
        """Applies an impulse to the game object.This will apply the specified impulse to the game object at the specified point.
        If point != position, applyImpulse will also change the objects angular momentum.
        Otherwise, only linear momentum will change.

                :param point: the point to apply the impulse to (in world or local coordinates)
                :param impulse: impulse vector.
                :param local: False: you get the "global" impulse ie: relative to world coordinates with world orientation.

        True: you get the "local" impulse ie: relative to local coordinates with object orientation.

        Default to False if not passed.
        """

    def setDamping(self, linear_damping, angular_damping) -> None:
        """Sets both the `linearDamping` and `angularDamping` simultaneously. This is more efficient than setting both properties individually.

        :param linear_damping: Linear ("translational") damping factor.
        :param angular_damping: Angular ("rotational") damping factor.
        """

    def suspendPhysics(self, freeConstraints: bool) -> None:
        """Suspends physics for this object.

                :param freeConstraints: When set to True physics constraints used by the object are deleted.
        Else when False (the default) constraints are restored when restoring physics.
        """

    def restorePhysics(self) -> None:
        """Resumes physics for this object. Also reinstates collisions."""

    def suspendDynamics(self, ghost: bool) -> None:
        """Suspends dynamics physics for this object.:py:attr:`isSuspendDynamics` allows you to inspect whether the object is in a suspended state.

                :param ghost: When set to True, collisions with the object will be ignored, similar to the "ghost" checkbox in
        Blender. When False (the default), the object becomes static but still collide with other objects.
        """

    def restoreDynamics(self) -> None:
        """Resumes dynamics physics for this object. Also reinstates collisions; the object will no longer be a ghost."""

    def enableRigidBody(self) -> None:
        """Enables rigid body physics for this object.Rigid body physics allows the object to roll on collisions."""

    def disableRigidBody(self) -> None:
        """Disables rigid body physics for this object."""

    def setCcdMotionThreshold(self, ccd_motion_threshold) -> None:
        """Sets `ccdMotionThreshold` that is the delta of movement that has to happen in one physics tick to trigger the continuous motion detection.

        :param ccd_motion_threshold: delta of movement.
        """

    def setCcdSweptSphereRadius(self, ccd_swept_sphere_radius) -> None:
        """Sets `ccdSweptSphereRadius` that is the radius of the sphere that is used to check for possible collisions when ccd is activated.

        :param ccd_swept_sphere_radius: sphere radius.
        """

    def setParent(self, parent, compound: bool = True, ghost: bool = True) -> None:
        """Sets this objects parent.
        Control the shape status with the optional compound and ghost parameters:In that case you can control if it should be ghost or not:

                :param parent: new parent object.
                :param compound: whether the shape should be added to the parent compound shape.

        True: the object shape should be added to the parent compound shape.

        False: the object should keep its individual shape.
                :param ghost: whether the object should be ghost while parented.

        True: if the object should be made ghost while parented.

        False: if the object should be solid while parented.
        """

    def removeParent(self) -> None:
        """Removes this objects parent."""

    def getPhysicsId(self) -> None:
        """Returns the user data object associated with this game objects physics controller."""

    def getPropertyNames(self) -> list:
        """Gets a list of all property names.

        :return: All property names for this object.
        """

    def getDistanceTo(self, other) -> float:
        """

        :param other: a point or another `~bge.types.KX_GameObject` to measure the distance to.
        :return: distance to another object or point.
        """

    def getVectTo(self, other) -> None:
        """Returns the vector and the distance to another object or point.
        The vector is normalized unless the distance is 0, in which a zero length vector is returned.

                :param other: a point or another `~bge.types.KX_GameObject` to get the vector and distance to.
                :return: (distance, globalVector(3), localVector(3))
        """

    def rayCastTo(self, other, dist: float = 0, prop: str = "") -> None:
        """Look towards another point/object and find first object hit within dist that matches prop.The ray is always casted from the center of the object, ignoring the object itself.
        The ray is casted towards the center of another object or an explicit [x, y, z] point.
        Use rayCast() if you need to retrieve the hit point

                :param other: [x, y, z] or object towards which the ray is casted
                :param dist: max distance to look (can be negative => look behind); 0 or omitted => detect up to other
                :param prop: property name that object must have; can be omitted => detect any object
                :return: the first object hit or None if no object or object does not match prop
        """

    def rayCast(
        self,
        objto,
        objfrom=None,
        dist: float = 0,
        prop: str = "",
        face: int = False,
        xray: int = False,
        poly: int = 0,
        mask=65535,
    ) -> None:
        """Look from a point/object to another point/object and find first object hit within dist that matches prop.
        if poly is 0, returns a 3-tuple with object reference, hit point and hit normal or (None, None, None) if no hit.
        if poly is 1, returns a 4-tuple with in addition a `~bge.types.KX_PolyProxy` as 4th element.
        if poly is 2, returns a 5-tuple with in addition a 2D vector with the UV mapping of the hit point as 5th element.The face parameter determines the orientation of the normal.The ray has X-Ray capability if xray parameter is 1, otherwise the first object hit (other than self object) stops the ray.
        The prop and xray parameters interact as follow.The `~bge.types.KX_PolyProxy` 4th element of the return tuple when poly=1 allows to retrieve information on the polygon hit by the ray.
        If there is no hit or the hit object is not a static mesh, None is returned as 4th element.The ray ignores collision-free objects and faces that dont have the collision flag enabled, you can however use ghost objects.

                :param objto: [x, y, z] or object to which the ray is casted
                :param objfrom: [x, y, z] or object from which the ray is casted; None or omitted => use self object center
                :param dist: max distance to look (can be negative => look behind); 0 or omitted => detect up to to
                :param prop: property name that object must have; can be omitted or "" => detect any object
                :param face: normal option: 1=>return face normal; 0 or omitted => normal is oriented towards origin
                :param xray: X-ray option: 1=>skip objects that dont match prop; 0 or omitted => stop on first object
                :param poly: polygon option: 0, 1 or 2 to return a 3-, 4- or 5-tuple with information on the face hit.

        0 or omitted: return value is a 3-tuple (object, hitpoint, hitnormal) or (None, None, None) if no hit

        1: return value is a 4-tuple and the 4th element is a `~bge.types.KX_PolyProxy` or None if no hit or the object doesnt use a mesh collision shape.

        2: return value is a 5-tuple and the 5th element is a 2-tuple (u, v) with the UV mapping of the hit point or None if no hit, or the object doesnt use a mesh collision shape, or doesnt have a UV mapping.
                :param mask: collision mask: The collision mask (16 layers mapped to a 16-bit integer) is combined with each objects collision group, to hit only a subset of the objects in the scene. Only those objects for which collisionGroup & mask is true can be hit.
                :return: (object, hitpoint, hitnormal) or (object, hitpoint, hitnormal, polygon) or (object, hitpoint, hitnormal, polygon, hituv).

        object, hitpoint and hitnormal are None if no hit.

        polygon is valid only if the object is valid and is a static object, a dynamic object using mesh collision shape or a soft body object, otherwise it is None

        hituv is valid only if polygon is valid and the object has a UV mapping, otherwise it is None
        """

    def collide(
        self, obj: str | typing_extensions.Self
    ) -> list[KX_CollisionContactPoint]:
        """Test if this object collides object `obj`.

                :param obj: the object to test collision with
                :return: (collide, points)

        collide, True if this object collides object `obj`

        points, contact point data of the collision or None
        """

    def setCollisionMargin(self, margin: float) -> None:
        """Set the objects collision margin.

        :param margin: the collision margin distance in blender units.
        """

    def sendMessage(self, subject: str, body: str = "", to: str = "") -> None:
        """Sends a message.

        :param subject: The subject of the message
        :param body: The body of the message (optional)
        :param to: The name of the object to send the message to (optional)
        """

    def reinstancePhysicsMesh(
        self,
        gameObject: str | None = "",
        meshObject: str | None = "",
        dupli: bool | None = False,
        evaluated: bool | None = False,
    ) -> bool:
        """Updates the physics system with the changed mesh.If no arguments are given the physics mesh will be re-created from the first mesh assigned to the game object.

        :param gameObject: optional argument, set the physics shape from this gameObjets mesh.
        :param meshObject: optional argument, set the physics shape from this mesh.
        :param dupli: optional argument, duplicate the physics shape.
        :param evaluated: optional argument, use evaluated object physics shape (Object with modifiers applied).
        :return: True if reinstance succeeded, False if it failed.
        """

    def replacePhysicsShape(self, gameObject: str) -> bool:
        """Replace the current physics shape.

        :param gameObject: set the physics shape from this gameObjets.
        :return: True if replace succeeded, False if it failed.
        """

    def get(self, key, default) -> None:
        """Return the value matching key, or the default value if its not found.
        :arg key: the matching key
        :type key: string
        :arg default: optional default value is the key isnt matching, defaults to None if no value passed.
        :return: The key value or a default.

                :param key:
                :param default:
        """

    def playAction(
        self,
        name: str,
        start_frame,
        end_frame,
        layer: int = 0,
        priority: int = 0,
        blendin: float = 0,
        play_mode: int = KX_ACTION_MODE_PLAY,
        layer_weight: float = 0.0,
        ipo_flags=0,
        speed: float = 1.0,
        blend_mode: int = KX_ACTION_BLEND_BLEND,
    ) -> None:
        """Plays an action.

        :param name: the name of the action.
        :param start_frame:
        :param end_frame:
        :param layer: the layer the action will play in (actions in different layers are added/blended together).
        :param priority: only play this action if there isnt an action currently playing in this layer with a higher (lower number) priority.
        :param blendin: the amount of blending between this animation and the previous one on this layer.
        :param play_mode: the play mode. one of `these constants <gameobject-playaction-mode>`.
        :param layer_weight: how much of the previous layer to use for blending.
        :param ipo_flags: flags for the old IPO behaviors (force, etc).
        :param speed: the playback speed of the action as a factor (1.0 = normal speed, 2.0 = 2x speed, etc).
        :param blend_mode: how to blend this layer with previous layers. one of `these constants <gameobject-playaction-blend>`.
        """

    def stopAction(self, layer: int) -> None:
        """Stop playing the action on the given layer.

        :param layer: The layer to stop playing, defaults to 0 if no value passed.
        """

    def getActionFrame(self, layer: int) -> float:
        """Gets the current frame of the action playing in the supplied layer.

        :param layer: The layer that you want to get the frame from, defaults to 0 if no value passed.
        :return: The current frame of the action
        """

    def getActionName(self, layer: int) -> str:
        """Gets the name of the current action playing in the supplied layer.

        :param layer: The layer that you want to get the action name from, defaults to 0 if no value passed.
        :return: The name of the current action
        """

    def setActionFrame(self, frame: float, layer: int) -> None:
        """Set the current frame of the action playing in the supplied layer.

        :param frame: The frame to set the action to
        :param layer: The layer where you want to set the frame, defaults to 0 if no value passed.
        """

    def isPlayingAction(self, layer: int) -> bool:
        """Checks to see if there is an action playing in the given layer.

        :param layer: The layer to check for a playing action, defaults to 0 if no value passed.
        :return: Whether or not the action is playing
        """

    def addDebugProperty(self, name: str, debug: bool) -> None:
        """Adds a single debug property to the debug list.

        :param name: name of the property that added to the debug list.
        :param debug: the debug state, defaults to True if no value passed.
        """

class KX_LibLoadStatus:
    """Libload is deprecated since 0.3+. An object providing information about a LibLoad() operation."""

    onFinish: collections.abc.Callable
    """ A callback that gets called when the lib load is done."""

    finished: bool
    """ The current status of the lib load."""

    progress: float
    """ The current progress of the lib load as a normalized value from 0.0 to 1.0."""

    libraryName: str
    """ The name of the library being loaded (the first argument to LibLoad)."""

    timeTaken: float
    """ The amount of time, in seconds, the lib load took (0 until the operation is complete)."""

class KX_LightObject:
    """A Light game object.It is possible to use attributes from :type: `~bpy.types.Light`"""

class KX_LodLevel:
    """A single lod level for a game object lod manager.Return True if the lod level uses a different mesh than the original object mesh. (read only)type

    boolean0.3.0Return True if the lod level uses a different material than the original object mesh material. (read only)type

    boolean0.3.0
    """

    mesh: typing.Any
    """ The mesh used for this lod level. (read only)"""

    level: int
    """ The number of the lod level. (read only)"""

    distance: typing.Any
    """ Distance to begin using this level of detail. (read only)"""

    hysteresis: typing.Any
    """ Minimum distance factor change required to transition to the previous level of detail in percent. (read only)"""

    useMesh: typing.Any
    useMaterial: typing.Any
    useHysteresis: bool
    """ Return true if the lod level uses hysteresis override. (read only)"""

class KX_LodManager:
    """This class contains a list of all levels of detail used by a game object."""

    levels: typing.Any
    """ Return the list of all levels of detail of the lod manager."""

    distanceFactor: float
    """ Method to multiply the distance to the camera."""

class KX_MeshProxy:
    """A mesh object.You can only read the vertex properties of a mesh object. In upbge 0.3+, KX_MeshProxy,
    KX_PolyProxy, and KX_VertexProxy are only a representation of the physics shape as it was
    when it was converted in BL_DataConversion.
    Previously this kind of meshes were used both for render and physics, but since 0.3+,
    it is only useful in limited cases. In most cases, bpy API should be used instead.Note:
    The physics simulation doesnt currently update KX_Mesh/Poly/VertexProxy.The correct method of iterating over every `~bge.types.KX_VertexProxy` in a game object
    """

    materials: typing.Any
    numPolygons: int
    numMaterials: int
    polygons: typing.Any
    """ Returns the list of polygons of this mesh."""

    def getMaterialName(self, matid: int) -> str:
        """Gets the name of the specified material.

        :param matid: the specified material.
        :return: the attached material name.
        """

    def getTextureName(self, matid: int) -> str:
        """Gets the name of the specified materials texture.

        :param matid: the specified material
        :return: the attached materials texture name.
        """

    def getVertexArrayLength(self, matid: int) -> int:
        """Gets the length of the vertex array associated with the specified material.There is one vertex array for each material.

        :param matid: the specified material
        :return: the number of vertices in the vertex array.
        """

    def getVertex(self, matid: int, index: int) -> None:
        """Gets the specified vertex from the mesh object.

        :param matid: the specified material
        :param index: the index into the vertex array.
        :return: a vertex object.
        """

    def getPolygon(self, index: int) -> None:
        """Gets the specified polygon from the mesh.

        :param index: polygon number
        :return: a polygon object.
        """

class KX_NavMeshObject:
    """Python interface for using and controlling navigation meshes."""

    def findPath(self, start, goal) -> None:
        """Finds the path from start to goal points.

        :param start: the start point3D Vector3D Vector
        :param goal: the goal point
        :return: a path as a list of points
        """

    def raycast(self, start, goal) -> float:
        """Raycast from start to goal points.

        :param start: the start point3D Vector3D Vector
        :param goal: the goal point
        :return: the hit factor
        """

    def draw(self, mode) -> None:
        """Draws a debug mesh for the navigation mesh.

        :param mode: the drawing mode (one of `these constants <navmesh-draw-mode>`)integer
        :return: None
        """

    def rebuild(self) -> None:
        """Rebuild the navigation mesh.

        :return: None
        """

class KX_PolyProxy:
    """A polygon holds the index of the vertex forming the poylgon.
    You can only read the vertex properties of a mesh object. In upbge 0.3+, KX_MeshProxy,
    KX_PolyProxy, and KX_VertexProxy are only a representation of the physics shape as it was
    when it was converted in BL_DataConversion.
    Previously this kind of meshes were used both for render and physics, but since 0.3+,
    it is only useful in limited cases. In most cases, bpy API should be used instead.Note:
    The physics simulation doesnt currently update KX_Mesh/Poly/VertexProxy.
    """

    material_name: str
    """ The name of polygon material, empty if no material."""

    material: typing.Any
    """ The material of the polygon."""

    texture_name: str
    """ The texture name of the polygon."""

    material_id: int
    """ The material index of the polygon, use this to retrieve vertex proxy from mesh proxy."""

    v1: int
    """ vertex index of the first vertex of the polygon, use this to retrieve vertex proxy from mesh proxy."""

    v2: int
    """ vertex index of the second vertex of the polygon, use this to retrieve vertex proxy from mesh proxy."""

    v3: int
    """ vertex index of the third vertex of the polygon, use this to retrieve vertex proxy from mesh proxy."""

    v4: int
    """ Vertex index of the fourth vertex of the polygon, 0 if polygon has only 3 vertex
Use this to retrieve vertex proxy from mesh proxy."""

    visible: int
    """ visible state of the polygon: 1=visible, 0=invisible."""

    collide: int
    """ collide state of the polygon: 1=receives collision, 0=collision free."""

    vertices: typing.Any
    """ Returns the list of vertices of this polygon."""

    def getMaterialName(self) -> str:
        """Returns the polygon material name with MA prefix

        :return: material name
        """

    def getMaterial(self) -> None:
        """

        :return: The polygon material
        """

    def getTextureName(self) -> str:
        """

        :return: The texture name
        """

    def getMaterialIndex(self) -> int:
        """Returns the material bucket index of the polygon.
        This index and the ones returned by getVertexIndex() are needed to retrieve the vertex proxy from `~bge.types.KX_MeshProxy`.

                :return: the material index in the mesh
        """

    def getNumVertex(self) -> int:
        """Returns the number of vertex of the polygon.

        :return: number of vertex, 3 or 4.
        """

    def isVisible(self) -> bool:
        """Returns whether the polygon is visible or not

        :return: 0=invisible, 1=visible
        """

    def isCollider(self) -> int:
        """Returns whether the polygon is receives collision or not

        :return: 0=collision free, 1=receives collision
        """

    def getVertexIndex(self, vertex) -> int:
        """Returns the mesh vertex index of a polygon vertex
        This index and the one returned by getMaterialIndex() are needed to retrieve the vertex proxy from `~bge.types.KX_MeshProxy`.

                :param vertex: index of the vertex in the polygon: 0->3integer
                :return: mesh vertex index
        """

    def getMesh(self) -> None:
        """Returns a mesh proxy

        :return: mesh proxy
        """

class KX_PythonComponent:
    """Python component can be compared to python logic bricks with parameters.
    The python component is a script loaded in the UI, this script defined a component class by inheriting from `~bge.types.KX_PythonComponent`.
    This class must contain a dictionary of properties: `args` and two default functions: `start` and `update`.The script must have .py extension.The component properties are loaded from the `args` attribute from the UI at loading time.
    When the game start the function `start` is called with as arguments a dictionary of the properties name and value.
    The `update` function is called every frames during the logic stage before running logics bricks,
    the goal of this function is to handle and process everything.The following component example moves and rotates the object when pressing the keys W, A, S and D.Since the components are loaded for the first time outside the bge, then `bge` is a fake module that contains only the class
    `~bge.types.KX_PythonComponent` to avoid importing all the bge modules.
    This behavior is safer but creates some issues at loading when the user want to use functions or attributes from the bge modules other
    than the `~bge.types.KX_PythonComponent` class. The way is to not call these functions at loading outside the bge. To detect it, the bge
    module contains the attribute `__component__` when its imported outside the bge.The following component example add a "Cube" object at initialization and move it along x for each update. It shows that the user can
    use functions from scene and load the component outside the bge by setting global attributes in a condition at the beginning of the
    script.The property types supported are float, integer, boolean, string, set (for enumeration) and Vector 2D, 3D and 4D. The following example
    show all of these property types.
    """

    object: typing.Any
    """ The object owner of the component."""

    args: dict
    """ Dictionary of the component properties, the keys are string and the value can be: float, integer, Vector(2D/3D/4D), set, string."""

    logger: typing.Any
    """ A logger instance that can be used to log messages related to this object (read-only)."""

    loggerName: str
    """ A name used to create the logger instance. By default, it takes the form Type[Name]
and can be optionally overridden as below:"""

    def start(self, args: dict) -> None:
        """Initialize the component.

        :param args: The dictionary of the properties name and value.
        """

    def update(self) -> None:
        """Process the logic of the component."""

    def dispose(self) -> None:
        """Function called when the component is destroyed."""

class KX_Scene:
    """An active scene that gives access to objects, cameras, lights and scene attributes.The activity culling stuff is supposed to disable logic bricks when their owner gets too far
    from the active camera.  It was taken from some code lurking at the back of KX_Scene - who knows
    what it does!@bug: All attributes are read only at the moment.The override camera used for scene culling, if set to None the culling is proceeded with the camera used to render.type

    `~bge.types.KX_Camera` or None0.3.0The current active world, (read-only).type

    `~bge.types.KX_WorldInfo`0.3.0True if the scene is suspended, (read-only).type

    boolean0.3.0True when Dynamic Bounding box Volume Tree is set (read-only).type

    boolean0.3.0Suspends this scene.0.3.0Resume this scene.0.3.0
    """

    name: str
    """ The scene's name, (read-only)."""

    objects: typing.Any
    """ A list of objects in the scene, (read-only)."""

    objectsInactive: typing.Any
    """ A list of objects on background layers (used for the addObject actuator), (read-only)."""

    lights: typing.Any
    """ A list of lights in the scene, (read-only)."""

    cameras: typing.Any
    """ A list of cameras in the scene, (read-only)."""

    texts: typing.Any
    """ A list of texts in the scene, (read-only)."""

    active_camera: typing.Any
    """ The current active camera."""

    overrideCullingCamera: typing.Any
    world: typing.Any
    filterManager: typing.Any
    """ The scene's 2D filter manager, (read-only)."""

    suspended: typing.Any
    activityCulling: bool
    """ True if the scene allow object activity culling."""

    dbvt_culling: typing.Any
    pre_draw: list
    """ A list of callables to be run before the render step. The callbacks can take as argument the rendered camera."""

    post_draw: list
    """ A list of callables to be run after the render step."""

    pre_draw_setup: list
    """ A list of callables to be run before the drawing setup (i.e., before the model view and projection matrices are computed).
The callbacks can take as argument the rendered camera, the camera could be temporary in case of stereo rendering."""

    onRemove: list
    """ A list of callables to run when the scene is destroyed."""

    gravity: typing.Any
    """ The scene gravity using the world x, y and z axis."""

    logger: typing.Any
    """ A logger instance that can be used to log messages related to this object (read-only)."""

    loggerName: str
    """ A name used to create the logger instance. By default, it takes the form KX_Scene[Name]."""

    def addObject(
        self,
        object: str,
        reference: str | None = "",
        time: float = 0.0,
        dupli: bool = False,
    ) -> None:
        """Adds an object to the scene like the Add Object Actuator would.

        :param object: The (name of the) object to add.
        :param reference: The (name of the) object which position, orientation, and scale to copy (optional), if the object to add is a light and there is not reference the lights layer will be the same that the active layer in the blender scene.
        :param time: The lifetime of the added object, in frames (assumes one frame is 1/60 second). A time of 0.0 means the object will last forever (optional).
        :param dupli: Full duplication of object data (mesh, materials...).
        :return: The newly added object.
        """

    def end(self) -> None:
        """Removes the scene from the game."""

    def restart(self) -> None:
        """Restarts the scene."""

    def replace(self, scene: str) -> bool:
        """Replaces this scene with another one.

        :param scene: The name of the scene to replace this scene with.
        :return: True if the scene exists and was scheduled for addition, False otherwise.
        """

    def suspend(self) -> None: ...
    def resume(self) -> None: ...
    def get(self, key, default=None) -> None:
        """Return the value matching key, or the default value if its not found.
        :return: The key value or a default.

                :param key:
                :param default:
        """

    def drawObstacleSimulation(self) -> None:
        """Draw debug visualization of obstacle simulation."""

    def convertBlenderObject(self, blenderObject) -> None:
        """Converts a `~bpy.types.Object` into a `~bge.types.KX_GameObject` during runtime.
        For example, you can append an Object from another .blend file during bge runtime
        using: bpy.ops.wm.append(...) then convert this Object into a KX_GameObject to have
        logic bricks, physics... converted. This is meant to replace libload.

                :param blenderObject: The Object to be converted.
                :return: Returns the newly converted gameobject.
        """

    def convertBlenderObjectsList(self, blenderObjectsList, asynchronous: bool) -> None:
        """Converts all bpy.types.Object inside a python List into its correspondent `~bge.types.KX_GameObject` during runtime.
        For example, you can append an Object List during bge runtime using: ob = object_data_add(...) and ML.append(ob) then convert the Objects
        inside the List into several KX_GameObject to have logic bricks, physics... converted. This is meant to replace libload.
        The conversion can be asynchronous or synchronous.

                :param blenderObjectsList: The Object list to be converted.
                :param asynchronous: The Object list conversion can be asynchronous or not.
        """

    def convertBlenderCollection(self, blenderCollection, asynchronous: bool) -> None:
        """Converts all bpy.types.Object inside a Collection into its correspondent `~bge.types.KX_GameObject` during runtime.
        For example, you can append a Collection from another .blend file during bge runtime
        using: bpy.ops.wm.append(...) then convert the Objects inside the Collection into several KX_GameObject to have
        logic bricks, physics... converted. This is meant to replace libload. The conversion can be asynchronous
        or synchronous.

                :param blenderCollection: The collection to be converted.
                :param asynchronous: The collection conversion can be asynchronous or not.
        """

    def convertBlenderAction(self, Action) -> None:
        """Registers a bpy.types.Action into the bge logic manager to be abled to play it during runtime.
        For example, you can append an Action from another .blend file during bge runtime
        using: bpy.ops.wm.append(...) then register this Action to be abled to play it.

                :param Action: The Action to be converted.
        """

    def unregisterBlenderAction(self, Action) -> None:
        """Unregisters a bpy.types.Action from the bge logic manager.
        The unregistered action will still be in the .blend file
        but cant be played anymore with bge. If you want to completely
        remove the action you need to call bpy.data.actions.remove(Action, do_unlink=True)
        after you unregistered it from bge logic manager.

                :param Action: The Action to be unregistered.
        """

    def addOverlayCollection(self, kxCamera, blenderCollection) -> None:
        """Adds an overlay collection (as with collection actuator) to render this collection objects
        during a second render pass in overlay using the KX_Camera passed as argument.

                :param kxCamera: The camera used to render the overlay collection.
                :param blenderCollection: The overlay collection to add.
        """

    def removeOverlayCollection(self, blenderCollection) -> None:
        """Removes an overlay collection (as with collection actuator).

        :param blenderCollection: The overlay collection to remove.
        """

    def getGameObjectFromObject(self, blenderObject: bpy.types.Object) -> None:
        """Get the KX_GameObject corresponding to the blenderObject.

        :param blenderObject: the Object from which we want to get the KX_GameObject.
        """

class KX_VehicleWrapper:
    """KX_VehicleWrapperTODO - description"""

    rayMask: typing.Any
    """ Set ray cast mask."""

    def addWheel(
        self,
        wheel,
        attachPos,
        downDir,
        axleDir,
        suspensionRestLength: float,
        wheelRadius: float,
        hasSteering: bool,
    ) -> None:
        """Add a wheel to the vehicle

        :param wheel: The object to use as a wheel.
        :param attachPos: The position to attach the wheel, relative to the chassis object center.
        :param downDir: The direction vector pointing down to where the vehicle should collide with the floor.
        :param axleDir: The axis the wheel rotates around, relative to the chassis.
        :param suspensionRestLength: The length of the suspension when no forces are being applied.
        :param wheelRadius: The radius of the wheel (half the diameter).
        :param hasSteering: True if the wheel should turn with steering, typically used in front wheels.
        """

    def applyBraking(self, force: float, wheelIndex: int) -> None:
        """Apply a braking force to the specified wheel

        :param force: the brake force
        :param wheelIndex: index of the wheel where the force needs to be applied
        """

    def applyEngineForce(self, force: float, wheelIndex: int) -> None:
        """Apply an engine force to the specified wheel

        :param force: the engine force
        :param wheelIndex: index of the wheel where the force needs to be applied
        """

    def getConstraintId(self) -> int:
        """Get the constraint ID

        :return: the constraint id
        """

    def getConstraintType(self) -> int:
        """Returns the constraint type.

        :return: constraint type
        """

    def getNumWheels(self) -> int:
        """Returns the number of wheels.

        :return: the number of wheels for this vehicle
        """

    def getWheelOrientationQuaternion(self, wheelIndex: int) -> None:
        """Returns the wheel orientation as a quaternion.

        :param wheelIndex: the wheel index
        :return: TODO Description
        """

    def getWheelPosition(self, wheelIndex: int) -> list:
        """Returns the position of the specified wheel

        :param wheelIndex: the wheel index
        :return: position vector
        """

    def getWheelRotation(self, wheelIndex: int) -> float:
        """Returns the rotation of the specified wheel

        :param wheelIndex: the wheel index
        :return: the wheel rotation
        """

    def setRollInfluence(self, rollInfluece: float, wheelIndex: int) -> None:
        """Set the specified wheels roll influence.
        The higher the roll influence the more the vehicle will tend to roll over in corners.

                :param rollInfluece: the wheel roll influence
                :param wheelIndex: the wheel index
        """

    def setSteeringValue(self, steering: float, wheelIndex: int) -> None:
        """Set the specified wheels steering

        :param steering: the wheel steering
        :param wheelIndex: the wheel index
        """

    def setSuspensionCompression(self, compression: float, wheelIndex: int) -> None:
        """Set the specified wheels compression

        :param compression: the wheel compression
        :param wheelIndex: the wheel index
        """

    def setSuspensionDamping(self, damping: float, wheelIndex: int) -> None:
        """Set the specified wheels damping

        :param damping: the wheel damping
        :param wheelIndex: the wheel index
        """

    def setSuspensionStiffness(self, stiffness: float, wheelIndex: int) -> None:
        """Set the specified wheels stiffness

        :param stiffness: the wheel stiffness
        :param wheelIndex: the wheel index
        """

    def setTyreFriction(self, friction: float, wheelIndex: int) -> None:
        """Set the specified wheels tyre friction

        :param friction: the tyre friction
        :param wheelIndex: the wheel index
        """

class KX_VertexProxy:
    """A vertex holds position, UV, color and normal information.
    You can only read the vertex properties of a mesh object. In upbge 0.3+, KX_MeshProxy,
    KX_PolyProxy, and KX_VertexProxy are only a representation of the physics shape as it was
    when it was converted in BL_DataConversion.
    Previously this kind of meshes were used both for render and physics, but since 0.3+,
    it is only useful in limited cases. In most cases, bpy API should be used instead.Note:
    The physics simulation doesnt currently update KX_Mesh/Poly/VertexProxy.
    """

    XYZ: typing.Any
    """ The position of the vertex."""

    UV: typing.Any
    """ The texture coordinates of the vertex."""

    uvs: typing.Any
    """ The texture coordinates list of the vertex."""

    normal: typing.Any
    """ The normal of the vertex."""

    color: typing.Any
    """ The color of the vertex.Black = [0.0, 0.0, 0.0, 1.0], White = [1.0, 1.0, 1.0, 1.0]"""

    colors: typing.Any
    """ The color list of the vertex."""

    x: float
    """ The x coordinate of the vertex."""

    y: float
    """ The y coordinate of the vertex."""

    z: float
    """ The z coordinate of the vertex."""

    u: float
    """ The u texture coordinate of the vertex."""

    v: float
    """ The v texture coordinate of the vertex."""

    u2: float
    """ The second u texture coordinate of the vertex."""

    v2: float
    """ The second v texture coordinate of the vertex."""

    r: float
    """ The red component of the vertex color. 0.0 <= r <= 1.0."""

    g: float
    """ The green component of the vertex color. 0.0 <= g <= 1.0."""

    b: float
    """ The blue component of the vertex color. 0.0 <= b <= 1.0."""

    a: float
    """ The alpha component of the vertex color. 0.0 <= a <= 1.0."""

    def getXYZ(self) -> None:
        """Gets the position of this vertex.

        :return: this vertexes position in local coordinates.
        """

    def getUV(self) -> None:
        """Gets the UV (texture) coordinates of this vertex.

        :return: this vertexes UV (texture) coordinates.
        """

    def getUV2(self) -> None:
        """Gets the 2nd UV (texture) coordinates of this vertex.

        :return: this vertexes UV (texture) coordinates.
        """

    def getRGBA(self) -> int:
        """Gets the color of this vertex.The color is represented as four bytes packed into an integer value.  The color is
        packed as RGBA.Since Python offers no way to get each byte without shifting, you must use the struct module to
        access color in an machine independent way.Because of this, it is suggested you use the r, g, b and a attributes or the color attribute instead.

                :return: packed color. 4 byte integer with one byte per color channel in RGBA format.
        """

    def getNormal(self) -> None:
        """Gets the normal vector of this vertex.

        :return: normalized normal vector.
        """

class SCA_2DFilterActuator:
    """Create, enable and disable 2D filters.The following properties dont have an immediate effect.
    You must active the actuator to get the result.
    The actuator is not persistent: it automatically stops itself after setting up the filter
    but the filter remains active. To stop a filter you must activate the actuator with type
    set to `~bge.logic.RAS_2DFILTER_DISABLED` or `~bge.logic.RAS_2DFILTER_NOFILTER`.action on motion blur: 0=enable, 1=disable.type

    integer0.3.0argument for motion blur filter.type

    float (0.0-100.0)0.3.0
    """

    shaderText: str
    """ shader source code for custom shader."""

    disableMotionBlur: typing.Any
    mode: int
    """ Type of 2D filter, use one of `these constants <Two-D-FilterActuator-mode>`."""

    passNumber: typing.Any
    """ order number of filter in the stack of 2D filters. Filters are executed in increasing order of passNb.Only be one filter can be defined per passNb."""

    value: typing.Any

class SCA_ANDController:
    """An AND controller activates only when all linked sensors are activated.There are no special python methods for this controller."""

class SCA_ActionActuator:
    """Action Actuators apply an action to an actor."""

    action: str
    """ The name of the action to set as the current action."""

    frameStart: float
    """ Specifies the starting frame of the animation."""

    frameEnd: float
    """ Specifies the ending frame of the animation."""

    blendIn: float
    """ Specifies the number of frames of animation to generate when making transitions between actions."""

    priority: int
    """ Sets the priority of this actuator. Actuators will lower priority numbers will override actuators with higher numbers."""

    frame: float
    """ Sets the current frame for the animation."""

    propName: str
    """ Sets the property to be used in FromProp playback mode."""

    mode: int
    """ The operation mode of the actuator. Can be one of `these constants<action-actuator>`."""

    useContinue: bool
    """ The actions continue option, True or False. When True, the action will always play from where last left off,
otherwise negative events to this actuator will reset it to its start frame."""

    framePropName: str
    """ The name of the property that is set to the current frame number."""

class SCA_ActuatorSensor:
    """Actuator sensor detect change in actuator state of the parent object.
    It generates a positive pulse if the corresponding actuator is activated
    and a negative pulse if the actuator is deactivated.
    """

    actuator: str
    """ the name of the actuator that the sensor is monitoring."""

class SCA_AddObjectActuator:
    """Edit Object Actuator (in Add Object Mode)"""

    object: typing.Any
    """ the object this actuator adds."""

    objectLastCreated: typing.Any
    """ the last added object from this actuator (read-only)."""

    time: float
    """ the lifetime of added objects, in frames. Set to 0 to disable automatic deletion."""

    linearVelocity: typing.Any
    """ the initial linear velocity of added objects."""

    angularVelocity: typing.Any
    """ the initial angular velocity of added objects."""

    def instantAddObject(self) -> None:
        """adds the object without needing to calling SCA_PythonController.activate()"""

class SCA_AlwaysSensor:
    """This sensor is always activated."""

class SCA_ArmatureActuator:
    """Armature Actuators change constraint condition on armatures."""

    type: int
    """ The type of action that the actuator executes when it is active.Can be one of `these constants <armatureactuator-constants-type>`"""

    constraint: typing.Any
    """ The constraint object this actuator is controlling."""

    target: typing.Any
    """ The object that this actuator will set as primary target to the constraint it controls."""

    subtarget: typing.Any
    """ The object that this actuator will set as secondary target to the constraint it controls."""

    weight: typing.Any
    """ The weight this actuator will set on the constraint it controls."""

    influence: typing.Any
    """ The influence this actuator will set on the constraint it controls."""

class SCA_ArmatureSensor:
    """Armature sensor detect conditions on armatures."""

    type: int
    """ The type of measurement that the sensor make when it is active.Can be one of `these constants <armaturesensor-type>`"""

    constraint: typing.Any
    """ The constraint object this sensor is watching."""

    value: float
    """ The threshold used in the comparison with the constraint error
The linear error is only updated on CopyPose/Distance IK constraint with iTaSC solver
The rotation error is only updated on CopyPose+rotation IK constraint with iTaSC solver
The linear error on CopyPose is always >= 0: it is the norm of the distance between the target and the bone
The rotation error on CopyPose is always >= 0: it is the norm of the equivalent rotation vector between the bone and the target orientations
The linear error on Distance can be positive if the distance between the bone and the target is greater than the desired distance, and negative if the distance is smaller."""

class SCA_CameraActuator:
    """Applies changes to a camera."""

    damping: float
    """ strength of of the camera following movement."""

    axis: int
    """ The camera axis (0, 1, 2) for positive XYZ, (3, 4, 5) for negative XYZ."""

    min: float
    """ minimum distance to the target object maintained by the actuator."""

    max: float
    """ maximum distance to stay from the target object."""

    height: float
    """ height to stay above the target object."""

    object: typing.Any
    """ the object this actuator tracks."""

class SCA_CollisionSensor:
    """Collision sensor detects collisions between objects."""

    propName: str
    """ The property or material to collide with."""

    useMaterial: bool
    """ Determines if the sensor is looking for a property or material. KX_True = Find material; KX_False = Find property."""

    usePulseCollision: bool
    """ When enabled, changes to the set of colliding objects generate a pulse."""

    hitObject: typing.Any
    """ The last collided object. (read-only)."""

    hitObjectList: typing.Any
    """ A list of colliding objects. (read-only)."""

    hitMaterial: str
    """ The material of the object in the face hit by the ray. (read-only)."""

class SCA_ConstraintActuator:
    """A constraint actuator limits the position, rotation, distance or orientation of an object."""

    damp: int
    """ Time constant of the constraint expressed in frame (not use by Force field constraint)."""

    rotDamp: int
    """ Time constant for the rotation expressed in frame (only for the distance constraint), 0 = use damp for rotation as well."""

    direction: typing.Any
    """ The reference direction in world coordinate for the orientation constraint."""

    option: int
    """ Binary combination of `these constants <constraint-actuator-option>`"""

    time: int
    """ activation time of the actuator. The actuator disables itself after this many frame. If set to 0, the actuator is not limited in time."""

    propName: str
    """ the name of the property or material for the ray detection of the distance constraint."""

    min: float
    """ The lower bound of the constraint. For the rotation and orientation constraint, it represents radiant."""

    distance: float
    """ the target distance of the distance constraint."""

    max: float
    """ the upper bound of the constraint. For rotation and orientation constraints, it represents radiant."""

    rayLength: float
    """ the length of the ray of the distance constraint."""

    limit: int
    """ type of constraint. Use one of the `these constants <constraint-actuator-limit>`"""

class SCA_DelaySensor:
    """The Delay sensor generates positive and negative triggers at precise time,
    expressed in number of frames. The delay parameter defines the length of the initial OFF period. A positive trigger is generated at the end of this period.The duration parameter defines the length of the ON period following the OFF period.
    There is a negative trigger at the end of the ON period. If duration is 0, the sensor stays ON and there is no negative trigger.The sensor runs the OFF-ON cycle once unless the repeat option is set: the OFF-ON cycle repeats indefinitely (or the OFF cycle if duration is 0).Use `SCA_ISensor.reset <bge.types.SCA_ISensor.reset>` at any time to restart sensor.
    """

    delay: int
    """ length of the initial OFF period as number of frame, 0 for immediate trigger."""

    duration: int
    """ length of the ON period in number of frame after the initial OFF period.If duration is greater than 0, a negative trigger is sent at the end of the ON pulse."""

    repeat: int
    """ 1 if the OFF-ON cycle should be repeated indefinitely, 0 if it should run once."""

class SCA_DynamicActuator:
    """Dynamic Actuator."""

    mode: int
    """ the type of operation of the actuator, 0-4"""

    mass: float
    """ the mass value for the KX_DYN_SET_MASS operation."""

class SCA_EndObjectActuator:
    """Edit Object Actuator (in End Object mode)This actuator has no python methods."""

class SCA_GameActuator:
    """The game actuator loads a new .blend file, restarts the current .blend file or quits the game."""

    fileName: str
    """ the new .blend file to load."""

    mode: typing.Any
    """ The mode of this actuator. Can be on of `these constants <game-actuator>`"""

class SCA_IActuator:
    """Base class for all actuator logic bricks."""

class SCA_IController:
    """Base class for all controller logic bricks."""

    state: typing.Any
    """ The controllers state bitmask. This can be used with the GameObject's state to test if the controller is active."""

    sensors: typing.Any
    """ A list of sensors linked to this controller."""

    actuators: typing.Any
    """ A list of actuators linked to this controller."""

    useHighPriority: bool
    """ When set the controller executes always before all other controllers that dont have this set."""

class SCA_ILogicBrick:
    """Base class for all logic bricks."""

    executePriority: int
    """ This determines the order controllers are evaluated, and actuators are activated (lower priority is executed first)."""

    owner: typing.Any
    """ The game object this logic brick is attached to (read-only)."""

    name: str
    """ The name of this logic brick (read-only)."""

class SCA_IObject:
    """This class has no python functions"""

class SCA_ISensor:
    """Base class for all sensor logic bricks."""

    usePosPulseMode: bool
    """ Flag to turn positive pulse mode on and off."""

    useNegPulseMode: bool
    """ Flag to turn negative pulse mode on and off."""

    frequency: int
    """ The frequency for pulse mode sensors.Use `skippedTicks`0.0.1"""

    skippedTicks: int
    """ Number of logic ticks skipped between 2 active pulses"""

    level: bool
    """ level Option whether to detect level or edge transition when entering a state.
It makes a difference only in case of logic state transition (state actuator).
A level detector will immediately generate a pulse, negative or positive
depending on the sensor condition, as soon as the state is activated.
A edge detector will wait for a state change before generating a pulse.
note: mutually exclusive with `tap`, enabling will disable `tap`."""

    tap: bool
    """ When enabled only sensors that are just activated will send a positive event,
after this they will be detected as negative by the controllers.
This will make a key that's held act as if its only tapped for an instant.
note: mutually exclusive with `level`, enabling will disable `level`."""

    invert: bool
    """ Flag to set if this sensor activates on positive or negative events."""

    triggered: bool
    """ True if this sensor brick is in a positive state. (read-only)."""

    positive: bool
    """ True if this sensor brick is in a positive state. (read-only)."""

    pos_ticks: int
    """ The number of ticks since the last positive pulse (read-only)."""

    neg_ticks: int
    """ The number of ticks since the last negative pulse (read-only)."""

    status: int
    """ The status of the sensor (read-only): can be one of `these constants<sensor-status>`."""

    def reset(self) -> None:
        """Reset sensor internal state, effect depends on the type of sensor and settings.The sensor is put in its initial state as if it was just activated."""

class SCA_InputEvent:
    """Events for a keyboard or mouse input."""

    status: list[int]
    """ A list of existing status of the input from the last frame.
Can contain `bge.logic.KX_INPUT_NONE` and `bge.logic.KX_INPUT_ACTIVE`.
The list always contains one value.
The first value of the list is the last value of the list in the last frame. (read-only)"""

    queue: list[int]
    """ A list of existing events of the input from the last frame.
Can contain `bge.logic.KX_INPUT_JUST_ACTIVATED` and `bge.logic.KX_INPUT_JUST_RELEASED`.
The list can be empty. (read-only)"""

    values: list[int]
    """ A list of existing value of the input from the last frame.
For keyboard it contains 1 or 0 and for mouse the coordinate of the mouse or the movement of the wheel mouse.
The list contains always one value, the size of the list is the same than `queue` + 1 only for keyboard inputs.
The first value of the list is the last value of the list in the last frame. (read-only)Example to get the non-normalized mouse coordinates:"""

    inactive: bool
    """ True if the input was inactive from the last frame."""

    active: bool
    """ True if the input was active from the last frame."""

    activated: bool
    """ True if the input was activated from the last frame."""

    released: bool
    """ True if the input was released from the last frame.Example to execute some action when I click or release mouse left button:"""

    type: int
    """ The type of the input.
One of `these constants<keyboard-keys>`"""

class SCA_JoystickSensor:
    """This sensor detects player joystick events."""

    axisValues: list[int]
    """ The state of the joysticks axis as a list of values `numAxis` long. (read-only).Each specifying the value of an axis between -32767 and 32767 depending on how far the axis is pushed, 0 for nothing.
The first 2 values are used by most joysticks and gamepads for directional control. 3rd and 4th values are only on some joysticks and can be used for arbitrary controls."""

    axisSingle: int
    """ like `axisValues` but returns a single axis value that is set by the sensor. (read-only)."""

    hatValues: list[int]
    """ The state of the joysticks hats as a list of values `numHats` long. (read-only).Each specifying the direction of the hat from 1 to 12, 0 when inactive.Hat directions are as follows...Use `button` instead.0.2.2"""

    hatSingle: int
    """ Like `hatValues` but returns a single hat direction value that is set by the sensor. (read-only).Use `button` instead.0.2.2"""

    numAxis: int
    """ The number of axes for the joystick at this index. (read-only)."""

    numButtons: int
    """ The number of buttons for the joystick at this index. (read-only)."""

    numHats: int
    """ The number of hats for the joystick at this index. (read-only).Use `numButtons` instead.0.2.2"""

    connected: bool
    """ True if a joystick is connected at this joysticks index. (read-only)."""

    index: int
    """ The joystick index to use (from 0 to 7). The first joystick is always 0."""

    threshold: int
    """ Axis threshold. Joystick axis motion below this threshold wont trigger an event. Use values between (0 and 32767), lower values are more sensitive."""

    button: int
    """ The button index the sensor reacts to (first button = 0). When the "All Events" toggle is set, this option has no effect."""

    axis: [int, int]
    """ The axis this sensor reacts to, as a list of two values [axisIndex, axisDirection]"""

    hat: [int, int]
    """ The hat the sensor reacts to, as a list of two values: [hatIndex, hatDirection]Use `button` instead.0.2.2"""

    def getButtonActiveList(self) -> list:
        """

        :return: A list containing the indicies of the currently pressed buttons.
        """

    def getButtonStatus(self, buttonIndex: int) -> bool:
        """

        :param buttonIndex: the button index, 0=first button
        :return: The current pressed state of the specified button.
        """

class SCA_KeyboardSensor:
    """A keyboard sensor detects player key presses.See module `bge.events` for keycode values."""

    key: int
    """ The key code this sensor is looking for. Expects a keycode from `bge.events` module."""

    hold1: int
    """ The key code for the first modifier this sensor is looking for. Expects a keycode from `bge.events` module."""

    hold2: int
    """ The key code for the second modifier this sensor is looking for. Expects a keycode from `bge.events` module."""

    toggleProperty: str
    """ The name of the property that indicates whether or not to log keystrokes as a string."""

    targetProperty: str
    """ The name of the property that receives keystrokes in case in case a string is logged."""

    useAllKeys: bool
    """ Flag to determine whether or not to accept all keys."""

    inputs: dict
    """ A list of pressed input keys that have either been pressed, or just released, or are active this frame. (read-only)."""

    events: typing.Any
    """ a list of pressed keys that have either been pressed, or just released, or are active this frame. (read-only).Use `inputs`0.2.2"""

    def getKeyStatus(self, keycode: int) -> int:
        """Get the status of a key.

        :param keycode: The code that represents the key you want to get the state of, use one of `these constants<keyboard-keys>`
        :return: The state of the given key, can be one of `these constants<input-status>`
        """

class SCA_MouseActuator:
    """The mouse actuator gives control over the visibility of the mouse cursor and rotates the parent object according to mouse movement."""

    visible: bool
    """ The visibility of the mouse cursor."""

    use_axis_x: bool
    """ Mouse movement along the x axis effects object rotation."""

    use_axis_y: bool
    """ Mouse movement along the y axis effects object rotation."""

    threshold: typing.Any
    """ Amount of movement from the mouse required before rotation is triggered.The values in the list should be between 0.0 and 0.5."""

    reset_x: bool
    """ Mouse is locked to the center of the screen on the x axis."""

    reset_y: bool
    """ Mouse is locked to the center of the screen on the y axis."""

    object_axis: typing.Any
    """ The object's 3D axis to rotate with the mouse movement. ([x, y])"""

    local_x: bool
    """ Rotation caused by mouse movement along the x axis is local."""

    local_y: bool
    """ Rotation caused by mouse movement along the y axis is local."""

    sensitivity: typing.Any
    """ The amount of rotation caused by mouse movement along the x and y axis.Negative values invert the rotation."""

    limit_x: typing.Any
    """ The minimum and maximum angle of rotation caused by mouse movement along the x axis in degrees.
limit_x[0] is minimum, limit_x[1] is maximum."""

    limit_y: typing.Any
    """ The minimum and maximum angle of rotation caused by mouse movement along the y axis in degrees.
limit_y[0] is minimum, limit_y[1] is maximum."""

    angle: typing.Any
    """ The current rotational offset caused by the mouse actuator in degrees."""

    def reset(self) -> None:
        """Undoes the rotation caused by the mouse actuator."""

class SCA_MouseFocusSensor:
    """The mouse focus sensor detects when the mouse is over the current game object.The mouse focus sensor works by transforming the mouse coordinates from 2d device
    space to 3d space then raycasting away from the camera.
    """

    raySource: typing.Any
    """ The worldspace source of the ray (the view position)."""

    rayTarget: typing.Any
    """ The worldspace target of the ray."""

    rayDirection: typing.Any
    """ The `rayTarget` - `raySource` normalized."""

    hitObject: typing.Any
    """ the last object the mouse was over."""

    hitPosition: typing.Any
    """ The worldspace position of the ray intersection."""

    hitNormal: typing.Any
    """ the worldspace normal from the face at point of intersection."""

    hitUV: typing.Any
    """ the UV coordinates at the point of intersection.If the object has no UV mapping, it returns [0, 0].The UV coordinates are not normalized, they can be < 0 or > 1 depending on the UV mapping."""

    usePulseFocus: bool
    """ When enabled, moving the mouse over a different object generates a pulse. (only used when the 'Mouse Over Any' sensor option is set)."""

    useXRay: bool
    mask: typing.Any
    """ The collision mask (16 layers mapped to a 16-bit integer) combined with each object's collision group, to hit only a subset of the
objects in the scene. Only those objects for which collisionGroup & mask is true can be hit."""

    propName: str
    useMaterial: bool

class SCA_MouseSensor:
    """Mouse Sensor logic brick."""

    position: [int, int]
    """ current [x, y] coordinates of the mouse, in frame coordinates (pixels)."""

    mode: int
    """ sensor mode. one of the following constants:"""

    def getButtonStatus(self, button: int) -> int:
        """Get the mouse button status.

        :param button: The code that represents the key you want to get the state of, use one of `these constants<mouse-keys>`
        :return: The state of the given key, can be one of `these constants<input-status>`
        """

class SCA_NANDController:
    """An NAND controller activates when all linked sensors are not active.There are no special python methods for this controller."""

class SCA_NORController:
    """An NOR controller activates only when all linked sensors are de-activated.There are no special python methods for this controller."""

class SCA_NearSensor:
    """A near sensor is a specialised form of touch sensor."""

    distance: float
    """ The near sensor activates when an object is within this distance."""

    resetDistance: float
    """ The near sensor deactivates when the object exceeds this distance."""

class SCA_NetworkMessageActuator:
    """Message Actuator"""

    propName: str
    """ Messages will only be sent to objects with the given property name."""

    subject: str
    """ The subject field of the message."""

    body: str
    """ The body of the message."""

    usePropBody: bool
    """ Send a property instead of a regular body message."""

class SCA_NetworkMessageSensor:
    """The Message Sensor logic brick.Currently only loopback (local) networks are supported."""

    subject: str
    """ The subject the sensor is looking for."""

    frameMessageCount: int
    """ The number of messages received since the last frame. (read-only)."""

    subjects: list[str]
    """ The list of message subjects received. (read-only)."""

    bodies: list[str]
    """ The list of message bodies received. (read-only)."""

class SCA_ORController:
    """An OR controller activates when any connected sensor activates.There are no special python methods for this controller."""

class SCA_ObjectActuator:
    """The object actuator ("Motion Actuator") applies force, torque, displacement, angular displacement,
    velocity, or angular velocity to an object.
    Servo control allows to regulate force to achieve a certain speed target.
    """

    force: typing.Any
    """ The force applied by the actuator."""

    useLocalForce: bool
    """ A flag specifying if the force is local."""

    torque: typing.Any
    """ The torque applied by the actuator."""

    useLocalTorque: bool
    """ A flag specifying if the torque is local."""

    dLoc: typing.Any
    """ The displacement vector applied by the actuator."""

    useLocalDLoc: bool
    """ A flag specifying if the dLoc is local."""

    dRot: typing.Any
    """ The angular displacement vector applied by the actuator"""

    useLocalDRot: bool
    """ A flag specifying if the dRot is local."""

    linV: typing.Any
    """ The linear velocity applied by the actuator."""

    useLocalLinV: bool
    """ A flag specifying if the linear velocity is local."""

    angV: typing.Any
    """ The angular velocity applied by the actuator."""

    useLocalAngV: bool
    """ A flag specifying if the angular velocity is local."""

    damping: typing.Any
    """ The damping parameter of the servo controller."""

    forceLimitX: typing.Any
    """ The min/max force limit along the X axis and activates or deactivates the limits in the servo controller."""

    forceLimitY: typing.Any
    """ The min/max force limit along the Y axis and activates or deactivates the limits in the servo controller."""

    forceLimitZ: typing.Any
    """ The min/max force limit along the Z axis and activates or deactivates the limits in the servo controller."""

    pid: list[float]
    """ The PID coefficients of the servo controller."""

    reference: typing.Any
    """ The object that is used as reference to compute the velocity for the servo controller."""

class SCA_ParentActuator:
    """The parent actuator can set or remove an objects parent object."""

    object: typing.Any
    """ the object this actuator sets the parent too."""

    mode: typing.Any
    """ The mode of this actuator."""

    compound: bool
    """ Whether the object shape should be added to the parent compound shape when parenting.Effective only if the parent is already a compound shape."""

    ghost: bool
    """ Whether the object should be made ghost when parenting
Effective only if the shape is not added to the parent compound shape."""

class SCA_PropertyActuator:
    """Property Actuator"""

    propName: str
    """ the property on which to operate."""

    value: str
    """ the value with which the actuator operates."""

    mode: int
    """ TODO - add constants to game logic dict!."""

class SCA_PropertySensor:
    """Activates when the game object property matches."""

    mode: int
    """ Type of check on the property. Can be one of `these constants <logic-property-sensor>`"""

    propName: str
    """ the property the sensor operates."""

    value: str
    """ the value with which the sensor compares to the value of the property."""

    min: str
    """ the minimum value of the range used to evaluate the property when in interval mode."""

    max: str
    """ the maximum value of the range used to evaluate the property when in interval mode."""

class SCA_PythonController:
    """A Python controller uses a Python script to activate its actuators,
    based on its sensors.
    """

    owner: typing.Any
    """ The object the controller is attached to."""

    script: str
    """ The value of this variable depends on the execution method."""

    mode: int
    """ the execution mode for this controller (read-only)."""

    def activate(self, actuator: str) -> None:
        """Activates an actuator attached to this controller.

        :param actuator: The actuator to operate on. Expects either an actuator instance or its name.
        """

    def deactivate(self, actuator: str) -> None:
        """Deactivates an actuator attached to this controller.

        :param actuator: The actuator to operate on. Expects either an actuator instance or its name.
        """

class SCA_PythonJoystick:
    """A Python interface to a joystick."""

    name: str
    """ The name assigned to the joystick by the operating system. (read-only)"""

    activeButtons: list
    """ A list of active button values. (read-only)"""

    axisValues: list[int]
    """ The state of the joysticks axis as a list of values `numAxis` long. (read-only).Each specifying the value of an axis between -1.0 and 1.0
depending on how far the axis is pushed, 0 for nothing.
The first 2 values are used by most joysticks and gamepads for directional control.
3rd and 4th values are only on some joysticks and can be used for arbitrary controls."""

    hatValues: typing.Any
    """ Use `activeButtons` instead.0.2.2"""

    numAxis: int
    """ The number of axes for the joystick at this index. (read-only)."""

    numButtons: int
    """ The number of buttons for the joystick at this index. (read-only)."""

    numHats: typing.Any
    """ Use `numButtons` instead.0.2.2"""

    strengthLeft: typing.Any
    """ Strength of the Low frequency joystick's motor (placed at left position usually)."""

    strengthRight: typing.Any
    """ Strength of the High frequency joystick's motor (placed at right position usually)."""

    duration: typing.Any
    """ Duration of the vibration in milliseconds."""

    isVibrating: typing.Any
    """ Check status of joystick vibration"""

    hasVibration: typing.Any
    """ Check if the joystick supports vibration"""

    def startVibration(self) -> None:
        """Starts the vibration.

        :return: None
        """

    def stopVibration(self) -> None:
        """Stops the vibration.

        :return: None
        """

class SCA_PythonKeyboard:
    """The current keyboard."""

    inputs: dict
    """ A dictionary containing the input of each keyboard key. (read-only)."""

    events: dict
    """ A dictionary containing the status of each keyboard event or key. (read-only).Use `inputs`.0.2.2"""

    activeInputs: dict
    """ A dictionary containing the input of only the active keyboard keys. (read-only)."""

    active_events: dict
    """ A dictionary containing the status of only the active keyboard events or keys. (read-only).Use `activeInputs`.0.2.2"""

    text: str
    """ The typed unicode text from the last frame."""

    def getClipboard(self) -> str:
        """Gets the clipboard text.

        :return:
        """

    def setClipboard(self, text: str) -> None:
        """Sets the clipboard text.

        :param text: New clipboard text
        """

class SCA_PythonMouse:
    """The current mouse."""

    inputs: dict
    """ A dictionary containing the input of each mouse event. (read-only)."""

    events: dict
    """ a dictionary containing the status of each mouse event. (read-only).Use `inputs`.0.2.2"""

    activeInputs: dict
    """ A dictionary containing the input of only the active mouse events. (read-only)."""

    active_events: dict
    """ a dictionary containing the status of only the active mouse events. (read-only).Use `activeInputs`.0.2.2"""

    position: typing.Any
    """ The normalized x and y position of the mouse cursor."""

    visible: bool
    """ The visibility of the mouse cursor."""

class SCA_RadarSensor:
    """Radar sensor is a near sensor with a conical sensor object."""

    coneOrigin: list[float]
    """ The origin of the cone with which to test. The origin is in the middle of the cone. (read-only)."""

    coneTarget: list[float]
    """ The center of the bottom face of the cone with which to test. (read-only)."""

    distance: float
    """ The height of the cone with which to test (read-only)."""

    angle: float
    """ The angle of the cone (in degrees) with which to test (read-only)."""

    axis: typing.Any
    """ The axis on which the radar cone is cast.KX_RADAR_AXIS_POS_X, KX_RADAR_AXIS_POS_Y, KX_RADAR_AXIS_POS_Z,
KX_RADAR_AXIS_NEG_X, KX_RADAR_AXIS_NEG_Y, KX_RADAR_AXIS_NEG_Z"""

class SCA_RandomActuator:
    """Random Actuator"""

    seed: int
    """ Seed of the random number generator.Equal seeds produce equal series. If the seed is 0, the generator will produce the same value on every call."""

    para1: float
    """ the first parameter of the active distribution.Refer to the documentation of the generator types for the meaning of this value."""

    para2: float
    """ the second parameter of the active distribution.Refer to the documentation of the generator types for the meaning of this value."""

    distribution: int
    """ Distribution type. (read-only). Can be one of `these constants <logic-random-distributions>`"""

    propName: str
    """ the name of the property to set with the random value.If the generator and property types do not match, the assignment is ignored."""

    def setBoolConst(self, value: bool) -> None:
        """Sets this generator to produce a constant boolean value.

        :param value: The value to return.
        """

    def setBoolUniform(self) -> None:
        """Sets this generator to produce a uniform boolean distribution.The generator will generate True or False with 50% chance."""

    def setBoolBernouilli(self, value: float) -> None:
        """Sets this generator to produce a Bernouilli distribution.

                :param value: Specifies the proportion of False values to produce.

        0.0: Always generate True

        1.0: Always generate False
        """

    def setIntConst(self, value: int) -> None:
        """Sets this generator to always produce the given value.

        :param value: the value this generator produces.
        """

    def setIntUniform(self, lower_bound: int, upper_bound: int) -> None:
        """Sets this generator to produce a random value between the given lower and
        upper bounds (inclusive).

                :param lower_bound:
                :param upper_bound:
        """

    def setIntPoisson(self, value: float) -> None:
        """Generate a Poisson-distributed number.This performs a series of Bernouilli tests with parameter value.
        It returns the number of tries needed to achieve success.

                :param value:
        """

    def setFloatConst(self, value: float) -> None:
        """Always generate the given value.

        :param value:
        """

    def setFloatUniform(self, lower_bound: float, upper_bound: float) -> None:
        """Generates a random float between lower_bound and upper_bound with a
        uniform distribution.

                :param lower_bound:
                :param upper_bound:
        """

    def setFloatNormal(self, mean: float, standard_deviation: float) -> None:
        """Generates a random float from the given normal distribution.

        :param mean: The mean (average) value of the generated numbers
        :param standard_deviation: The standard deviation of the generated numbers.
        """

    def setFloatNegativeExponential(self, half_life: float) -> None:
        """Generate negative-exponentially distributed numbers.The half-life time is characterized by half_life.

        :param half_life:
        """

class SCA_RandomSensor:
    """This sensor activates randomly."""

    lastDraw: int
    """ The seed of the random number generator."""

    seed: int
    """ The seed of the random number generator."""

class SCA_RaySensor:
    """A ray sensor detects the first object in a given direction."""

    propName: str
    """ The property the ray is looking for."""

    range: float
    """ The distance of the ray."""

    useMaterial: bool
    """ Whether or not to look for a material (false = property)."""

    useXRay: bool
    """ Whether or not to use XRay."""

    mask: typing.Any
    """ The collision mask (16 layers mapped to a 16-bit integer) combined with each object's collision group, to hit only a subset of the
objects in the scene. Only those objects for which collisionGroup & mask is true can be hit."""

    hitObject: typing.Any
    """ The game object that was hit by the ray. (read-only)."""

    hitPosition: typing.Any
    """ The position (in worldcoordinates) where the object was hit by the ray. (read-only)."""

    hitNormal: typing.Any
    """ The normal (in worldcoordinates) of the object at the location where the object was hit by the ray. (read-only)."""

    hitMaterial: str
    """ The material of the object in the face hit by the ray. (read-only)."""

    rayDirection: typing.Any
    """ The direction from the ray (in worldcoordinates). (read-only)."""

    axis: typing.Any
    """ The axis the ray is pointing on."""

class SCA_ReplaceMeshActuator:
    """Edit Object actuator, in Replace Mesh mode."""

    mesh: typing.Any
    """ `~bge.types.KX_MeshProxy` or the name of the mesh that will replace the current one.Set to None to disable actuator."""

    useDisplayMesh: bool
    """ when true the displayed mesh is replaced."""

    usePhysicsMesh: bool
    """ when true the physics mesh is replaced."""

    def instantReplaceMesh(self) -> None:
        """Immediately replace mesh without delay."""

class SCA_SceneActuator:
    """Scene Actuator logic brick."""

    scene: str
    """ the name of the scene to change to/overlay/underlay/remove/suspend/resume."""

    camera: str
    """ the camera to change to."""

    useRestart: bool
    """ Set flag to True to restart the sene."""

    mode: typing.Any
    """ The mode of the actuator."""

class SCA_SoundActuator:
    """Sound Actuator.The `startSound`, `pauseSound` and `stopSound` do not require the actuator to be activated - they act instantly provided that the actuator has been activated once at least."""

    volume: float
    """ The volume (gain) of the sound."""

    time: float
    """ The current position in the audio stream (in seconds)."""

    pitch: float
    """ The pitch of the sound."""

    mode: int
    """ The operation mode of the actuator. Can be one of `these constants<logic-sound-actuator>`"""

    sound: aud.Sound
    """ The sound the actuator should play."""

    is3D: bool
    """ Whether or not the actuator should be using 3D sound. (read-only)"""

    preload: bool
    """ Control whether to keep a RAM-buffered copy for fast re-triggers"""

    volume_maximum: float
    """ The maximum gain of the sound, no matter how near it is."""

    volume_minimum: float
    """ The minimum gain of the sound, no matter how far it is away."""

    distance_reference: float
    """ The distance where the sound has a gain of 1.0."""

    distance_maximum: float
    """ The maximum distance at which you can hear the sound."""

    attenuation: float
    """ The influence factor on volume depending on distance."""

    cone_angle_inner: float
    """ The angle of the inner cone."""

    cone_angle_outer: float
    """ The angle of the outer cone."""

    cone_volume_outer: float
    """ The gain outside the outer cone (the gain in the outer cone will be interpolated between this value and the normal gain in the inner cone)."""

    def startSound(self) -> None:
        """Starts the sound.

        :return: None
        """

    def pauseSound(self) -> None:
        """Pauses the sound.

        :return: None
        """

    def stopSound(self) -> None:
        """Stops the sound.

        :return: None
        """

class SCA_StateActuator:
    """State actuator changes the state mask of parent object."""

    operation: int
    """ Type of bit operation to be applied on object state mask.You can use one of `these constants <state-actuator-operation>`"""

    mask: int
    """ Value that defines the bits that will be modified by the operation.The bits that are 1 in the mask will be updated in the object state.The bits that are 0 are will be left unmodified expect for the Copy operation which copies the mask to the object state."""

class SCA_SteeringActuator:
    """Steering Actuator for navigation."""

    behavior: int
    """ The steering behavior to use. One of `these constants <logic-steering-actuator>`."""

    velocity: float
    """ Velocity magnitude"""

    acceleration: float
    """ Max acceleration"""

    turnspeed: float
    """ Max turn speed"""

    distance: float
    """ Relax distance"""

    target: typing.Any
    """ Target object"""

    navmesh: typing.Any
    """ Navigation mesh"""

    selfterminated: bool
    """ Terminate when target is reached"""

    enableVisualization: bool
    """ Enable debug visualization"""

    lockZVelocity: bool
    """ Disable simulation of linear motion along z axis"""

    pathUpdatePeriod: int
    """ Path update period"""

    pathLerpFactor: float
    """ Interpolation to smooth steering when changing paths or between different directions of the same path"""

    path: list[mathutils.Vector]
    """ Path point list."""

class SCA_TrackToActuator:
    """Edit Object actuator in Track To mode."""

    object: typing.Any
    """ the object this actuator tracks."""

    time: int
    """ the time in frames with which to delay the tracking motion."""

    use3D: bool
    """ the tracking motion to use 3D."""

    upAxis: typing.Any
    """ The axis that points upward."""

    trackAxis: typing.Any
    """ The axis that points to the target object."""

class SCA_VibrationActuator:
    """Vibration Actuator."""

    joyindex: typing.Any
    """ Joystick index."""

    strengthLeft: typing.Any
    """ Strength of the Low frequency joystick's motor (placed at left position usually)."""

    strengthRight: typing.Any
    """ Strength of the High frequency joystick's motor (placed at right position usually)."""

    duration: typing.Any
    """ Duration of the vibration in milliseconds."""

    isVibrating: typing.Any
    """ Check status of joystick vibration"""

    hasVibration: typing.Any
    """ Check if the joystick supports vibration"""

    def startVibration(self) -> None:
        """Starts the vibration.

        :return: None
        """

    def stopVibration(self) -> None:
        """Stops the vibration.

        :return: None
        """

class SCA_VisibilityActuator:
    """Visibility Actuator."""

    visibility: bool
    """ whether the actuator makes its parent object visible or invisible."""

    useOcclusion: bool
    """ whether the actuator makes its parent object an occluder or not."""

    useRecursion: bool
    """ whether the visibility/occlusion should be propagated to all children of the object."""

class SCA_XNORController:
    """An XNOR controller activates when all linked sensors are the same (activated or inative).There are no special python methods for this controller."""

class SCA_XORController:
    """An XOR controller activates when there is the input is mixed, but not when all are on or off.There are no special python methods for this controller."""

class BL_Texture(EXP_Value):
    """This is kept for backward compatibility with some scripts (bindCode mainly)."""

    bindCode: int
    """ Texture bind code/Id/number."""

def addOffScreen(
    width: int | None = None, height: int | None = None, mipmap: bool = False
) -> None:
    """Register a custom off screen (framebuffer in 0.3+) to render the filter to.

    :param width: In 0.3+, always canvas width (optional).
    :param height: In 0.3+, always canvas height (optional).
    :param mipmap: True if the color texture generate mipmap at the end of the filter rendering (optional).
    """

def removeOffScreen() -> None:
    """Unregister the custom off screen (framebuffer in 0.3+) the filter render to."""

def setTexture(textureName: str = "", gputexture=None) -> None:
    """Set specified GPUTexture as uniform for the 2D filter.

        :param textureName: The name of the texture in the 2D filter code. For example if you declare:
    uniform sampler2D myTexture;
    you will have to call filter.setTexture("myTexture", gputex).
        :param gputexture: The gputexture (see gpu module documentation).
    """

mipmap: bool
""" Request mipmap generation of the render bgl_RenderedTexture texture.
"""

offScreen: typing.Any
""" The custom off screen (framebuffer in 0.3+) the filter render to (read-only).
"""
