import bpy
import bmesh
from . selection import (
    select_by_loc,
    select_inverse_by_loc,
    deselect_all,
    select)
from . utils import mode, view3d_find


def clear_vert_group(vert_group, obj):
    indexes = get_vert_indexes_in_vert_group(vert_group.name, obj)
    vert_group.remove(indexes)


def get_verts_with_material(obj, material_name):
    '''Returns a list of vert objects which belong to polys that have a material applied'''
    verts = set()
    mat_index = obj.material_slots.find(material_name)
    polys = obj.data.polygons

    for poly in polys:
        if poly.material_index == mat_index:
            verts = set(poly.vertices) | verts

    return verts


def get_vert_indexes_in_vert_group(vert_group_name, obj):
    '''returns a list of vert indexes in a vert group'''
    vg_index = obj.vertex_groups[vert_group_name].index
    vert_indices = [v.index for v in obj.data.vertices if vg_index in [vg.group for vg in v.groups]]
    return vert_indices


def get_verts_in_vert_group(vert_group_name, obj):
    '''return a list of vert objects in a vert group'''
    vg_index = obj.vertex_groups[vert_group_name].index
    verts = [v for v in obj.data.vertices if vg_index in [vg.group for vg in v.groups]]
    return verts


def remove_verts_from_group(vert_group_name, obj, vert_indices):
    '''object mode only'''
    obj.vertex_groups[vert_group_name].remove(vert_indices)


def add_verts_to_group(vert_group_name, obj, vert_indices):
    '''object mode only'''
    obj.vertex_groups[vert_group_name].add(vert_indices)


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
        poly_vertex_group_index = find_vertex_group_of_polygon(poly, obj)

        if poly_vertex_group_index == vertex_group_index:
            poly.material_index = material_index


def construct_displacement_mod_vert_group(obj, textured_vert_group_names):
    '''Constructs a vertex group from the passed in group names for use by displacement modifier.
    This ensures that only correct vertices are being displaced.'''

    disp_mod_vert_group = obj.vertex_groups.new(name='disp_mod_vert_group')
    all_vert_groups = obj.vertex_groups

    for group in all_vert_groups:
        if group.name in textured_vert_group_names:
            verts = get_verts_in_vert_group(group.name, obj)
            indices = [i.index for i in verts]
            disp_mod_vert_group.add(index=indices, weight=1, type='ADD')
    return disp_mod_vert_group.name


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
