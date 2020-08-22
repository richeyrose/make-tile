from math import radians
import bpy
import bmesh
from mathutils import Vector
from ..utils.selection import in_bbox


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
    obj['penstate'] = True

    # create vertex groups
    if vert_groups:
        for i in range(len(vert_groups)):
            obj.vertex_groups.new(name=vert_groups[i])

    # link object to active collection
    bpy.context.layer_collection.collection.objects.link(obj)

    # make object active
    bpy.context.view_layer.objects.active = obj

    # update depgraph
    bpy.context.view_layer.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    '''
    vert = bmesh.ops.create_vert(bm, co=turtle.location)
    vert['vert'][0].select = True
    '''
    return bm, obj


def add_vert(bm):
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

    bpy.context.view_layer.objects.active['penstate'] = False


def pd(bm):
    """Pen Down.
    Deselect all verts and set bmesh owning object's penstate property to 'Trur'

    Args:
        bm (bmesh): bmesh
    """
    bpy.context.view_layer.objects.active['penstate'] = True


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
    extrude_translate(bm, (0.0, 0.0, distance), del_original)
    """Move Up.
    Moves turtle up along its positive local z axis. If object's penstate is down (True) then also extrudes
    any selected vaerts / edges / faces

    Args:
        bm (bmesh): bmesh
        distance (float): distance
        del_original (bool, optional): Whether to delete original faces when extruding. Defaults to True.
    """

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


def extrude_translate(bm, local_trans, del_original=True):
    """Extrudes and translates selected verts, edges or faces

    Args:
        bm (bmesh): bmesh
        local_trans (Vector[3]): Local transform vector
        del_original (bool, optional): Whether to delete original faces. Defaults to True.
    """
    # use cursor as turtle
    turtle = bpy.context.scene.cursor

    # work out transform in turtle's local space and convert to global
    local_trans = Vector(local_trans)
    world_trans = turtle.matrix.to_3x3() @ local_trans
    turtle.location = turtle.matrix.translation + world_trans

    if bpy.context.view_layer.objects.active['penstate'] is 1:
        if bm.select_mode == {'VERT'}:
            bm.select_flush(True)
            # get selected verts
            selected = [v for v in bm.verts if v.select]
            ret = bmesh.ops.extrude_vert_indiv(bm, verts=selected)
            verts = ret['verts']

            # translate along turtle's local Y
            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            # deselect original verts
            for v in bm.verts:
                v.select_set(False)
            bm.select_flush(False)

            # select extruded verts
            for v in verts:
                v.select_set(True)
            bm.select_flush(True)

        if bm.select_mode == {'EDGE'}:
            bm.select_flush(True)
            selected = [e for e in bm.edges if e.select]
            ret = bmesh.ops.extrude_edge_only(bm, edges=selected)
            geom = ret["geom"]
            edges = [e for e in geom
                     if isinstance(e, bmesh.types.BMEdge)]
            verts = [v for v in geom
                     if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            # deselect original edges
            for e in bm.edges:
                e.select_set(False)
            for v in bm.verts:
                v.select_set(False)
            bm.select_flush(False)

            # select extruded edges
            for e in edges:
                e.select_set(True)
            bm.select_flush(True)

        if bm.select_mode == {'FACE'}:
            bm.select_flush(True)
            sel_f = [f for f in bm.faces if f.select]
            ret = bmesh.ops.extrude_face_region(bm, geom=sel_f)
            geom = ret["geom"]

            faces = [f for f in geom
                     if isinstance(f, bmesh.types.BMFace)]
            edges = [e for e in geom
                     if isinstance(e, bmesh.types.BMEdge)]
            verts = [v for v in geom
                     if isinstance(v, bmesh.types.BMVert)]

            bmesh.ops.translate(bm, vec=(world_trans), verts=verts)

            if del_original is True:
                bmesh.ops.delete(bm, geom=sel_f, context='FACES')

            # deselect original faces and edges
            bm_deselect_all(bm)

            # select extruded faces
            for f in faces:
                f.select_set(True)


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
    Rotates the tortle right around its Z axis

    Args:
        degrees (float): degrees
    """
    lt(-degrees)


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


def bm_select_all(bm):
    """Select all verts.

    Args:
        bm (bmesh): bmesh
    """
    for v in bm.verts:
        v.select_set(True)
    bm.select_flush(True)


def bm_deselect_all(bm):
    """Deselect all verts.

    Args:
        bm (bmesh): bmesh
    """
    for v in bm.verts:
        v.select_set(False)
    bm.select_flush(False)


def draw_cuboid(dimensions):
    """Draw a cuboid.

    Args:
        dimensions (Vactor[3]): dimensions

    Returns:
        obj: bpy.types.Object
    """
    bm, obj = create_turtle(name='cuboid')
    add_vert(bm)
    bm.select_mode = {'VERT'}
    fd(bm, dimensions[1])
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    ri(bm, dimensions[0])
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, dimensions[2], False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_straight_wall_core(dims, subdivs, margin=0.001):
    vert_groups = ['Left', 'Right', 'Front', 'Back', 'Top', 'Bottom']

    bm, obj = create_turtle('Straight Wall', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    bottom_verts = []
    top_verts = []
    pd(bm)
    add_vert(bm)
    bm.select_mode = {'VERT'}
    ri(bm, margin)

    subdiv_x_dist = (dims[0] - (margin * 2)) / subdivs[0]

    i = 0
    while i < subdivs[0]:
        ri(bm, subdiv_x_dist)
        i += 1

    ri(bm, margin)
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    fd(bm, margin)

    subdiv_y_dist = (dims[1] - (margin * 2)) / subdivs[1]

    i = 0
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist)
        i += 1

    fd(bm, margin)

    for v in bm.verts:
        bottom_verts.append(v)

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, margin, False)

    subdiv_z_dist = (dims[2] - (margin * 2)) / subdivs[2]

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    up(bm, margin)
    top_verts = [v for v in bm.verts if v.select]

    for v in top_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[4] = 1

    for v in bottom_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[5] = 1

    pu(bm)
    home(obj)

    # select left and assign to vert group
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = 0.001

    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select
    left_verts = [v for v in bm.verts if v.select]

    for v in left_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[0] = 1

    # select right and assign to vert group
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = 0.001

    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select
    right_verts = [v for v in bm.verts if v.select]

    for v in right_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[1] = 1

    # select front and assign to vert group
    lbound = (margin, 0, margin)
    ubound = (dims[0] - margin, 0, dims[2] - margin)
    buffer = 0.0001

    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select
    front_verts = [v for v in bm.verts if v.select]

    for v in front_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[2] = 1

    # select back and assign to vert group
    lbound = (margin, dims[1], margin)
    ubound = (dims[0] - margin, dims[1], dims[2] - margin)
    buffer = 0.0001

    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select
    back_verts = [v for v in bm.verts if v.select]

    for v in back_verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[3] = 1

    finalise_turtle(bm, obj)
    return obj
