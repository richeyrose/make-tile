from math import pi, radians
import bpy
import bmesh
from .helpers import extrude_translate

def create_turtle(name, vert_groups=None):
    """Creates a mesh object and associated bmesh to pass to bmturtle functions

    Args:
        name (str): Object name
        vert_groups (list[str], optional): Names of vertex groups to create. Defaults to None.

    Returns:
        tuple: bmesh, object
    """
    turtle = bpy.context.scene.cursor
    # create new empty turtle world
    mesh = bpy.data.meshes.new("mesh")
    obj = bpy.data.objects.new(name, mesh)
    props = obj.mt_object_props
    props.penstate = True
    #obj['penstate'] = True

    # create vertex groups
    if vert_groups:
        for i in range(len(vert_groups)):
            obj.vertex_groups.new(name=vert_groups[i])

    # link object to active collection
    bpy.context.layer_collection.collection.objects.link(obj)

    # make object active
    bpy.context.view_layer.objects.active = obj

    # update depgraph
    #bpy.context.view_layer.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)

    return bm, obj


def add_vert(bm):
    """Add a vertice at the turtle location

    Args:
        bm (bmesh): bmesh
    """
    turtle = bpy.context.scene.cursor
    vert = bmesh.ops.create_vert(bm, co=turtle.location)
    vert['vert'][0].select = True


def pu(bm):
    """Pen Up.
    Deselect all verts and set bmesh owning object's penstate property to 'False'

    Args:
        bm (bmesh): bmesh
    """
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)

    bpy.context.view_layer.objects.active.mt_object_props.penstate = False
    # bpy.context.view_layer.objects.active['penstate'] = False


def pd(bm):
    """Pen Down.
    Deselect all verts and set bmesh owning object's penstate property to 'True'

    Args:
        bm (bmesh): bmesh
    """
    bpy.context.view_layer.objects.active.mt_object_props.penstate = True


def fd(bm, distance, del_original=True):
    """Move Forward.
    Moves turtle forward along its positive local y axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (0.0, distance, 0.0), del_original)


def bk(bm, distance, del_original=True):
    """Move Backward.
    Moves turtle backward along its negative local y axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (0.0, -distance, 0.0), del_original)


def up(bm, distance, del_original=True):
    """Move Up.
    Moves turtle up along its positive local z axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (0.0, 0.0, distance), del_original)


def dn(bm, distance, del_original=True):
    """Move Down.
    Moves turtle down along its negative local z axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (0.0, 0.0, -distance), del_original)


def ri(bm, distance, del_original=True):
    """Move Right.
    Moves turtle right along its positive local x axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (distance, 0.0, 0.0), del_original)


def lf(bm, distance, del_original=True):
    """Move Left.
    Moves turtle left along its negative local x axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """
    extrude_translate(bm, (-distance, 0.0, 0.0), del_original)


def ylf(degrees):
    """Yaw Left.
    Rotates the turtlke around the y axis.

    Args:
        degrees ([type]): [description]
    """
    yri(-degrees)


def yri(degrees):
    """Yaw Right.
    Rotates the turtle around the y axis.

    Args:
        degrees ([type]): [description]
    """
    turtle = bpy.context.scene.cursor
    turtle.rotation_euler = (
        turtle.rotation_euler[0],
        turtle.rotation_euler[1] + radians(degrees),
        turtle.rotation_euler[2])


def ptu(degrees):
    """Pitch Up.
    Rotates the turtle around the X axis.

    Args:
        degrees (float): degrees
    """
    turtle = bpy.context.scene.cursor
    turtle.rotation_euler = (
        turtle.rotation_euler[0] + radians(degrees),
        turtle.rotation_euler[1],
        turtle.rotation_euler[2])

def ptd(degrees):
    """Pitch Up.
    Rotates the turtle around the Y axis.

    Args:
        degrees (float): degrees
    """
    ptu(-degrees)

def lt(degrees):
    """Left turn.
    Rotates the turtle left around its Z axis

    Args:
        degrees (float): degrees
    """
    turtle = bpy.context.scene.cursor
    turtle.rotation_euler = (
        turtle.rotation_euler[0],
        turtle.rotation_euler[1],
        turtle.rotation_euler[2] + radians(degrees))


def rt(degrees):
    """Right turn.
    Rotates the turtle right around its Z axis

    Args:
        degrees (float): degrees
    """
    lt(-degrees)


def arc(bm, radius, degrees, segments):
    """Draw and arc centered on the turtle.

    Args:
        radius (float): radius
        degrees (float): degrees of arc to draw
        segments (int): number of segments to draw
    """
    circ = 2 * pi * radius
    seg_length = circ / ((360 / degrees) * segments)
    rotation = degrees / segments

    turtle = bpy.context.scene.cursor
    start_loc = turtle.location.copy()
    start_rot = turtle.rotation_euler.copy()

    pu(bm)
    edges = [e for e in bm.edges]
    fd(bm, radius)
    add_vert(bm)
    pd(bm)
    rt(90)
    rt(rotation / 2)

    i = 0
    while i < segments:
        fd(bm, seg_length)
        rt(rotation)

        i += 1

    pu(bm)

    turtle.location = start_loc
    turtle.rotation_euler = start_rot
    return [e for e in bm.edges if e not in edges]

def home(obj):
    """Home turtle.
    Returns the turtle to its parent object's origin

    Args:
        obj (bpy.types.Object): parent object
    """
    turtle = bpy.context.scene.cursor
    turtle.location = obj.location
    turtle.rotation_euler = obj.rotation_euler


def finalise_turtle(bm, obj):
    """Copy bmesh to object and free bmesh

    Args:
        bm (bmesh): bmesh
        obj (bpy.types.Object): object
    """
    # Make face normals consitent
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()
