import bmesh
import bpy
from mathutils import Vector
from ..utils.selection import in_bbox


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


def select_verts_in_bounds(lbound, ubound, buffer, bm):
    """Select vertices within cubical boundary.

    Args:
        lbound (tuple[3]): Lower left corner of bounds
        ubound (tuble[3]): Upper left corner of bounds
        buffer (float): Buffer around bbox
        bm (bmesh): bmesh

    Returns:
        list[bmesh.verts]: List of verts
    """
    vert_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = [in_bbox(lbound, ubound, v, buffer) for v in vert_coords]

    for vert, select in zip(bm.verts, to_select):
        vert.select = select

    return [v for v in bm.verts if v.select]


def assign_verts_to_group(verts, obj, deform_groups, group_name):
    """Assigns verts to vertex group

    Args:
        verts (list[bmesh.verts]): List of verts
        obj (bpy.types.Object): object
        deform_groups (bmesh.types.BMLayerCollection): deform layer. Corresponds to vertex groups
        group_name (string): Vertex group name
    """
    group_index = obj.vertex_groups[group_name].index

    for v in verts:
        if v.is_valid:
            groups = v[deform_groups]
            groups[group_index] = 1


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
