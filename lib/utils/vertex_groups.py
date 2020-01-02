from math import sqrt, radians, degrees, cos, acos
import bpy
import bmesh
from . selection import select_by_loc, select_inverse_by_loc, deselect_all, select_all, select
from . utils import mode


def get_selected_face_indices(obj):
    mesh = obj.data
    bm = bmesh.from_mesh(mesh)

    face_list = []
    for f in bm.faces:
        if f.select:
            face_list.append(f.index)

    return face_list


def find_vertex_group_of_polygon(polygon, obj):
    # Get all the vertex groups of all the vertices of this polygon
    all_vertex_groups = [g.group for v in polygon.vertices
                         for g in obj.data.vertices[v].groups]

    # Find the most frequent (mode) of all vertex groups
    counts = [all_vertex_groups.count(index) for index in all_vertex_groups]
    mode_index = counts.index(max(counts))
    av_mode = all_vertex_groups[mode_index]

    return av_mode


def assign_material_to_faces(obj, face_list, material_index):
    # find the current polygon's vertex group index
    for face in face_list:
        vertex_group_index = find_vertex_group_of_polygon(obj.data.polygons[face], obj)

    # iterate over all polys and change their material
    for poly in obj.data.polygons:
        poly_vertex_group_index = find_vertex_group_of_polygon(poly)

        if poly_vertex_group_index == vertex_group_index:
            poly.material_index = material_index


def corner_wall_to_vert_groups(obj, vert_locs):
    """Creates vertex groups out of passed in corner wall and locations of bottom verts
    Keyword Arguments:
    obj -- bpy.types.Object
    vert_locs -- DICT"""
    cursor_orig_loc = bpy.context.scene.cursor.location.copy()

    # make vertex groups
    obj.vertex_groups.new(name='End 1')  # leg 2 end
    obj.vertex_groups.new(name='End 2')  # leg 1 end
    obj.vertex_groups.new(name='Outer')  # outer
    obj.vertex_groups.new(name='Inner')  # inner
    obj.vertex_groups.new(name='Top')  # top
    obj.vertex_groups.new(name='Bottom')  # bottom

    mode('EDIT')
    deselect_all()

    # vert_locs keys
    leg_1_verts = ['c', 'b']
    leg_2_verts = ['e', 'f']
    outer_verts = ['a', 'b', 'e']
    inner_verts = ['c', 'd', 'f']
    bottom_verts = ['a', 'b', 'c', 'd', 'e', 'f']
    # top verts are at bottom vert location + obj.dimensions[2]

    for key, value in vert_locs.items():
        if key in leg_1_verts:
            select_by_loc(
                lbound=value,
                ubound=value,
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
            select_by_loc(
                lbound=(value[0], value[1], value[2] + obj.dimensions[2]),
                ubound=(value[0], value[1], value[2] + obj.dimensions[2]),
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='End 1')
        bpy.ops.object.vertex_group_assign()
        deselect_all()

    for key, value in vert_locs.items():
        if key in leg_2_verts:
            select_by_loc(
                lbound=value,
                ubound=value,
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
            select_by_loc(
                lbound=(value[0], value[1], value[2] + obj.dimensions[2]),
                ubound=(value[0], value[1], value[2] + obj.dimensions[2]),
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='End 2')
        bpy.ops.object.vertex_group_assign()
        deselect_all()

    for key, value in vert_locs.items():
        if key in bottom_verts:
            select_by_loc(
                lbound=value,
                ubound=value,
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='Bottom')
        bpy.ops.object.vertex_group_assign()
        deselect_all()

    for key, value in vert_locs.items():
        if key in bottom_verts:
            select_by_loc(
                lbound=(value[0], value[1], value[2] + obj.dimensions[2]),
                ubound=(value[0], value[1], value[2] + obj.dimensions[2]),
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='Top')
        bpy.ops.object.vertex_group_assign()
        deselect_all()

    for key, value in vert_locs.items():
        if key in outer_verts:
            select_by_loc(
                lbound=value,
                ubound=value,
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
            select_by_loc(
                lbound=(value[0], value[1], value[2] + obj.dimensions[2]),
                ubound=(value[0], value[1], value[2] + obj.dimensions[2]),
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='Outer')
        bpy.ops.object.vertex_group_assign()
        deselect_all()

    for key, value in vert_locs.items():
        if key in inner_verts:
            select_by_loc(
                lbound=value,
                ubound=value,
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
            select_by_loc(
                lbound=(value[0], value[1], value[2] + obj.dimensions[2]),
                ubound=(value[0], value[1], value[2] + obj.dimensions[2]),
                select_mode='VERT',
                coords='GLOBAL',
                additive=True
            )
        bpy.ops.object.vertex_group_set_active(group='Inner')
        bpy.ops.object.vertex_group_assign()
        deselect_all()


def curved_floor_to_vert_groups(obj, height, side_length):

    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')
    select(obj.name)
    mode('EDIT')

    deselect_all()
    select_by_loc(
        lbound=(obj.location),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2]),
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2] + height),
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1],
            obj.location[2] + height),
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_inverse_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side a')
    bpy.ops.object.vertex_group_assign()


def tri_prism_to_vert_groups(obj, dim, height):
    """Keyword arguments:
    obj - bpy.types.Object
    dim - DICT
    height - float"""
    # make vertex groups
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')

    mode('EDIT')

    deselect_all()
    select_by_loc(
        lbound=dim['loc_C'],
        ubound=(
            dim['loc_C'][0],
            dim['loc_C'][1],
            dim['loc_C'][2] + height),
        additive=True
    )
    select_by_loc(
        lbound=dim['loc_B'],
        ubound=(
            dim['loc_B'][0],
            dim['loc_B'][1],
            dim['loc_B'][2] + height),
        additive=True
    )
    bpy.ops.object.vertex_group_set_active(group='Side a')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=dim['loc_A'],
        ubound=(
            dim['loc_B'][0],
            dim['loc_B'][1],
            dim['loc_B'][2] + height),
        additive=True
    )
    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()

    select_by_loc(
        lbound=dim['loc_A'],
        ubound=(
            dim['loc_C'][0],
            dim['loc_C'][1],
            dim['loc_C'][2] + height)
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            dim['loc_A'][0],
            dim['loc_A'][1],
            dim['loc_A'][2] + height),
        ubound=(
            dim['loc_B'][0] + dim['a'],
            dim['loc_B'][1],
            dim['loc_B'][2] + height),
        additive=True
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            dim['loc_A'][0],
            dim['loc_A'][1],
            dim['loc_A'][2]),
        ubound=(
            dim['loc_B'][0] + dim['a'],
            dim['loc_B'][1],
            dim['loc_B'][2]),
        additive=True
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()


def cuboid_sides_to_vert_groups(obj):
    """makes a vertex group for each side of cuboid
    and assigns vertices to it"""

    mode('OBJECT')
    dim = obj.dimensions / 2

    # get original location of object origin and of cursor
    obj_original_loc = obj.location.copy()
    cursor_original_loc = bpy.context.scene.cursor.location.copy()

    # set origin to center of bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # make vertex groups
    obj.vertex_groups.new(name='Left')
    obj.vertex_groups.new(name='Right')
    obj.vertex_groups.new(name='Front')
    obj.vertex_groups.new(name='Back')
    obj.vertex_groups.new(name='Top')
    obj.vertex_groups.new(name='Bottom')

    mode('EDIT')

    # select X- and assign to X-
    select_by_loc(
        lbound=-dim,
        ubound=[-dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)

    bpy.ops.object.vertex_group_set_active(group='Left')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select X+ and assign to X+
    select_by_loc(
        lbound=[dim[0], -dim[1], -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Right')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y- and assign to Y-
    select_by_loc(
        lbound=-dim,
        ubound=[dim[0], -dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Front')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y+ and assign to Y+
    select_by_loc(
        lbound=[-dim[0], dim[1], -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Back')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z- and assign to Z-
    select_by_loc(
        lbound=-dim,
        ubound=[dim[0], dim[1], -dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z+ and assign to Z+
    select_by_loc(
        lbound=[-dim[0], -dim[1], dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    mode('OBJECT')

    # reset cursor and object origin
    bpy.context.scene.cursor.location = obj_original_loc
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = cursor_original_loc
