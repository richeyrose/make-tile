import os
import math
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, select_all, deselect_all, activate
from .. utils.registration import get_path, get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base
from . create_straight_wall_tile import create_openlock_straight_wall_base
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    add_displacement_mesh_modifiers,
    assign_displacement_materials,
    assign_preview_materials)


def create_rectangular_floor(
        tile_blueprint,
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        tile_material):

    """"Returns a floor
    Keyword arguments:
    tile_blueprint -- a blueprint consists of a tile type and base type
    tile_system -- tile system for slabs
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z],
    base_system -- tile system for bases
    tile_material -- material name
    """

    if base_system == 'OPENLOCK':
        base_size = Vector((tile_size[0], tile_size[1], .2756))
        tile_size[2] = 0.374
        base = create_openlock_base(tile_name, base_size)

    if base_system == 'PLAIN':
        base = create_plain_base(tile_name, base_size)

    if base_system == 'NONE':
        base_size = (0, 0, 0)

    if base:
        floor = create_floor(tile_name, tile_size, base_size, tile_material)


def create_plain_base(tile_name, base_size):
    '''Creates a plain cuboid base'''
    cursor_start_location = bpy.context.scene.cursor.location.copy()
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    base['geometry_type'] = 'BASE'
    base.location = (-base_size[0] / 2, -base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    mode('OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    base.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location
    return base


def create_floor(tile_name, tile_size, base_size, tile_material):
    ''''creates the preview and displacement slabs for the floor tile'''
    preview_slab = create_floor_slab(
        tile_name,
        tile_size,
        base_size,
        'PREVIEW')
    preview_slab['geometry_type'] = 'PREVIEW'

    displacement_slab = create_floor_slab(
        tile_name,
        tile_size,
        base_size,
        'DISPLACEMENT')
    displacement_slab['geometry_type'] = 'DISPLACEMENT'

    preview_slab['displacement_obj'] = displacement_slab
    displacement_slab['preview_obj'] = preview_slab

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_material]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials(displacement_slab, 'Z', 'z_pos', 'pos', [image_size, image_size], primary_material)
    assign_preview_materials(preview_slab, 'z_pos', primary_material, secondary_material)

    displacement_slab.hide_viewport = True


def create_floor_slab(tile_name, tile_size, base_size, geometry_type):
    """Returns a displacement or preview floor slab depending on the geometry type"""
    cursor_start_location = bpy.context.scene.cursor.location.copy()

    if geometry_type == 'PREVIEW':
        slab = create_preview_slab(tile_name, tile_size, base_size)
    else:
        slab = create_displacement_slab(tile_name, tile_size, base_size)
    slab['geometry_type'] = geometry_type

    slab.location = (-tile_size[0] / 2, -tile_size[1] / 2, base_size[2])

    bpy.context.scene.cursor.location = [0, 0, 0]
    mode('OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    select(slab.name)
    activate(slab.name)
    bpy.ops.uv.smart_project()
    cuboid_sides_to_vert_groups(slab)

    slab.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location

    return slab


def create_preview_slab(tile_name, tile_size, base_size):
    '''Returns the preview floor slab'''
    slab_size = Vector((tile_size[0], tile_size[1], tile_size[2] - base_size[2]))
    slab = draw_cuboid(slab_size)
    slab.name = tile_name + '.slab.preview'
    add_object_to_collection(slab, tile_name)
    return slab


def create_displacement_slab(tile_name, tile_size, base_size):
    '''Returns the displacement floor slab'''
    slab_size = Vector((tile_size[0], tile_size[1], 0.01))
    slab = draw_cuboid(slab_size)
    slab.name = tile_name + '.slab.displacement'
    add_object_to_collection(slab, tile_name)
    return slab


def create_openlock_base(
        tile_name,
        base_size):
    '''Creates an openlock style base'''
    if base_size[0] >= 1 and base_size[1] < 1 and base_size[1] > 0.496:
        # if base is less than an inch wide use a wall type base
        base = create_openlock_straight_wall_base(tile_name, base_size)
    elif base_size[0] < 1 or base_size[1] <= 0.496:
        # TODO: Display message in viewport
        print('Tile too small')
        col = bpy.data.collections[tile_name]
        bpy.data.collections.remove(col)
        return False
    else:
        base = draw_openlock_rect_floor_base(base_size)
        base.name = tile_name + '.base'
        add_object_to_collection(base, tile_name)
        clip_cutters = create_openlock_base_clip_cutter(base, tile_name)

        for clip_cutter in clip_cutters:
            matrixcopy = clip_cutter.matrix_world.copy()
            clip_cutter.parent = base
            clip_cutter.matrix_world = matrixcopy
            clip_cutter.display_type = 'BOUNDS'
            clip_cutter.hide_viewport = True
            clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
            clip_cutter_bool.operation = 'DIFFERENCE'
            clip_cutter_bool.object = clip_cutter

    mode('OBJECT')
    base['geometry_type'] = 'BASE'
    return base


def create_openlock_base_clip_cutter(base, tile_name):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- base the cutter will be used on
    tile_name -- the tile name
    """
    mode('OBJECT')

    base_size = base.dimensions.copy()
    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    # get location of bottom front left corner of tile
    front_left = Vector((
        base_location[0] - (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        base_location[2]))

    clip_cutter.location = (
        front_left[0] + 0.5,
        front_left[1] + 0.25,
        front_left[2])

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base_size[0] - 1

    select(clip_cutter.name)
    activate(clip_cutter.name)
    mirror_mod = clip_cutter.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = False
    mirror_mod.use_axis[1] = True
    mirror_mod.mirror_object = base

    clip_cutter2 = clip_cutter.copy()
    add_object_to_collection(clip_cutter2, tile_name)
    clip_cutter2.rotation_euler = (0, 0, math.radians(90))

    front_right = Vector((
        base_location[0] + (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        base_location[2]))

    clip_cutter2.location = (
        front_right[0] - 0.25,
        front_right[1] + 0.5,
        front_right[2])

    array_mod2 = clip_cutter2.modifiers['Array']
    array_mod2.fit_type = 'FIT_LENGTH'
    array_mod2.fit_length = base_size[1] - 1
    mirror_mod2 = clip_cutter2.modifiers['Mirror']
    mirror_mod2.use_axis[0] = True
    mirror_mod2.use_axis[1] = False

    # TODO: See if there's a low level equiv
    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

    return [clip_cutter, clip_cutter2]
