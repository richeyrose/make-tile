import bpy
import bmesh
from mathutils import Vector


def select_all():
    """Selects all objects if in OBJECT mode or verts / edges / faces if in EDIT mode"""
    if bpy.context.object is None:
        return False
    if len(bpy.data.objects) != 0:
        current_mode = bpy.context.object.mode
        if current_mode == 'EDIT':
            bpy.ops.mesh.select_all(action="SELECT")
            return {'FINISHED'}
        if current_mode == 'OBJECT':
            bpy.ops.object.select_all(action="SELECT")
            return {'FINISHED'}

    return {'FINISHED'}


def deselect_all():
    """Deselects all objects if in OBJECT mode or verts / edges / faces if in EDIT mode"""
    if bpy.context.object is None:
        return False
    if len(bpy.data.objects) != 0:
        current_mode = bpy.context.object.mode
        if current_mode == 'EDIT':
            bpy.ops.mesh.select_all(action="DESELECT")
            return {'FINISHED'}
        if current_mode == 'OBJECT':
            bpy.ops.object.select_all(action="DESELECT")
            return {'FINISHED'}

    return {'FINSIHED'}


def select(obj_name):
    """select object by name"""
    bpy.data.objects[obj_name].select_set(True)


def activate(obj_name):
    """activate object by name """
    bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]


def get_local_bbox_center(obj):
    """gets local object center relative to origin"""
    local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    return local_bbox_center


def get_global_bbox_center(obj):
    """gets global object center"""
    local_bbox_center = get_local_bbox_center(obj)
    global_bbox_center = obj.matrix_world @ local_bbox_center
    return global_bbox_center


def in_bbox(lbound, ubound, vert, buffer=0.001):
    """Checks whether a vertex is within a bounding cube
    Keyword arguments:
    lbound -- VECTOR lower left of cuboid
    ubound -- VECTOR upper right of cuboid
    vert -- bmesh.vert vertex
    buffer -- FLOAT buffer distance to add to cuboid. Useful when checking if single vert is at location
    """
    return lbound[0] - buffer <= vert[0] <= ubound[0] + buffer and \
        lbound[1] - buffer <= vert[1] <= ubound[1] + buffer and \
        lbound[2] - buffer <= vert[2] <= ubound[2] + buffer


def select_by_loc(
        lbound=(0, 0, 0),
        ubound=(0, 0, 0),
        select_mode='VERT',
        coords='GLOBAL',
        buffer=0.001,
        additive=False):
    """select faces, edges or verts by location that are wholly
    within a bounding cuboid

    Keyword arguments:

    lbound -- lower left bound of bounding box
    ubound -- upper right bound of bounding box
    select_mode -- default 'VERT'
    coords -- default 'GLOBAL'
    buffer - buffer around selection default = 0.001
    """

    # set selection mode
    bpy.ops.mesh.select_mode(type=select_mode)
    # grab the transformation matrix
    world = bpy.context.object.matrix_world

    # instantiate a bmesh object and ensure lookup table (bm.faces.ensure... works for all)
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()

    # initialise list of verts and parts to be selected
    verts = []
    to_select = []

    # for VERT, EDGE or FACE
    # grab list of global or local coords
    # test if the piece is entirely within the rectangular
    # prism defined by lbound and ubound
    # select each piece that returned TRUE and deselect each piece that returned FALSE

    if select_mode == 'VERT':
        if coords == 'GLOBAL':
            [verts.append((world @ v.co).to_tuple())for v in bm.verts]
        elif coords == 'LOCAL':
            [verts.append(v.co.to_tuple())for v in bm.verts]

        [to_select.append(in_bbox(lbound, ubound, v, buffer))for v in verts]

        for vert_obj, select in zip(bm.verts, to_select):
            if additive:
                vert_obj.select |= select
            else:
                vert_obj.select = select

    if select_mode == 'EDGE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in e.verts]) for e in bm.edges]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in e.verts]) for e in bm.edges]

        [to_select.append(all(in_bbox(lbound, ubound, v, buffer)for v in e)) for e in verts]

        for edge_obj, select in zip(bm.edges, to_select):
            if additive:
                edge_obj.select |= select
            else:
                edge_obj.select = select

    if select_mode == 'FACE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in f.verts])for f in bm.faces]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in f.verts]) for f in bm.faces]

        [to_select.append(all(in_bbox(lbound, ubound, v, buffer) for v in f))for f in verts]

        for face_obj, select in zip(bm.faces, to_select):
            if additive:
                face_obj.select |= select
            else:
                face_obj.select = select

    # update the edit mesh so we get live highlighting
    bmesh.update_edit_mesh(bpy.context.object.data)


def select_inverse_by_loc(
        lbound=(0, 0, 0),
        ubound=(0, 0, 0),
        select_mode='VERT',
        coords='GLOBAL',
        buffer=0.001,
        additive=False):
    """selects faces, edges or verts by location that are not within
    a bounding cuboid

    Keyword arguments:

    lbound -- lower left bound of bounding box
    ubound -- upper right bound of bounding box
    select_mode -- default 'VERT'
    coords -- default 'GLOBAL'
    buffer - buffer around selection default = 0.001
    """

    # set selection mode
    bpy.ops.mesh.select_mode(type=select_mode)
    # grab the transformation matrix
    world = bpy.context.object.matrix_world

    # instantiate a bmesh object and ensure lookup table (bm.faces.ensure... works for all)
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()

    # initialise list of verts and parts to be selected
    verts = []
    to_select = []

    # for VERT, EDGE or FACE
    # grab list of global or local coords
    # test if the piece is entirely within the rectangular
    # prism defined by lbound and ubound
    # select each piece that returned TRUE and deselect each piece that returned FALSE

    if select_mode == 'VERT':
        if coords == 'GLOBAL':
            [verts.append((world @ v.co).to_tuple())for v in bm.verts]
        elif coords == 'LOCAL':
            [verts.append(v.co.to_tuple())for v in bm.verts]

        [to_select.append(in_bbox(lbound, ubound, v, buffer))for v in verts]

        for vert_obj, select in zip(bm.verts, to_select):
            if select is True:
                select = False
            else:
                select = True

            if additive:
                vert_obj.select |= select
            else:
                vert_obj.select = select

    if select_mode == 'EDGE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in e.verts]) for e in bm.edges]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in e.verts]) for e in bm.edges]

        [to_select.append(all(in_bbox(lbound, ubound, v, buffer)for v in e)) for e in verts]

        for edge_obj, select in zip(bm.edges, to_select):

            if select is True:
                select = False
            else:
                select = True

            if additive:
                edge_obj.select |= select
            else:
                edge_obj.select = select

    if select_mode == 'FACE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in f.verts])for f in bm.faces]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in f.verts]) for f in bm.faces]

        [to_select.append(all(in_bbox(lbound, ubound, v, buffer) for v in f))for f in verts]

        for face_obj, select in zip(bm.faces, to_select):

            if select is True:
                select = False
            else:
                select = True

            if additive:
                face_obj.select |= select
            else:
                face_obj.select = select

    # update the edit mesh so we get live highlighting
    bmesh.update_edit_mesh(bpy.context.object.data)
