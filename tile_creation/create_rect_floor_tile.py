import os
import math
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, activate
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base
from . create_straight_wall_tile import create_openlock_base as create_openlock_wall_base
from .. lib.utils.vertex_groups import (
    construct_displacement_mod_vert_group,
    rect_floor_to_vert_groups)
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)
from . create_displacement_mesh import create_displacement_object
from . generic import finalise_tile


def create_rectangular_floor(tile_props):
    """"Creates a rectangular floor"""
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    scene = bpy.context.scene
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    # Get base and main part blueprints
    base_blueprint = tile_props.base_blueprint
    main_part_blueprint = tile_props.main_part_blueprint

    # We store a list of meshes here because we're going to add
    # trimmer modifiers to all of them later but we don't yet
    # know the full dimensions of our tile
    tile_meshes = []

    if base_blueprint == 'PLAIN':
        base = create_plain_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'OPENLOCK':
        base = create_openlock_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'NONE':
        tile_props.base_size = (0, 0, 0)
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        add_object_to_collection(base, tile_props.tile_name)

    if main_part_blueprint == 'OPENLOCK':
        tile_props.tile_size[2] = 0.3
        preview_core, displacement_core = create_cores(base, tile_props)
        displacement_core.hide_viewport = True
        tile_meshes.extend([preview_core, displacement_core])

    if main_part_blueprint == 'PLAIN':
        preview_core, displacement_core = create_cores(base, tile_props)
        displacement_core.hide_viewport = True
        tile_meshes.extend([preview_core, displacement_core])

    if main_part_blueprint == 'NONE':
        tile_props.tile_size = tile_props.base_size
        preview_core = None

    finalise_tile(
        base,
        preview_core,
        cursor_orig_loc)


def create_plain_base(tile_props):
    '''Creates a plain cuboid base'''
    cursor_start_location = bpy.context.scene.cursor.location.copy()
    base = draw_cuboid(tile_props.base_size)
    base.name = tile_props.tile_name + '.base'
    add_object_to_collection(base, tile_props.tile_name)

    base.mt_object_props.geometry_type = 'BASE'
    base.location = (-tile_props.base_size[0] / 2, -tile_props.base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    mode('OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    base.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    return base


def create_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    core = draw_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    core.name = tile_props.tile_name + '.core'
    add_object_to_collection(core, tile_props.tile_name)
    mode('OBJECT')

    core.location = (
        core.location[0] - tile_size[0] / 2,
        core.location[1] - tile_size[1] / 2,
        core.location[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    # create loops at each side of tile which we'll use
    # to prevent materials projecting beyond edges
    mode('EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(tile_size[0] / 2 - 0.001, 0, 0),
        plane_no=(1, 0, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(cursor_start_loc[0] - tile_size[0] / 2 + 0.001, 0, 0),
        plane_no=(1, 0, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, tile_size[1] / 2 - 0.001, 0),
        plane_no=(0, 1, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, cursor_start_loc[1] - tile_size[1] / 2 + 0.001, 0),
        plane_no=(0, 1, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, tile_size[2] - 0.001),
        plane_no=(0, 0, 1))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, cursor_start_loc[2] + base_size[2] + 0.001),
        plane_no=(0, 0, 1))
    mode('OBJECT')

    bpy.ops.uv.smart_project(ctx, island_margin=0.05)

    rect_floor_to_vert_groups(core)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def create_cores(base, tile_props):
    scene = bpy.context.scene

    preview_core = create_core(tile_props)
    preview_core, displacement_core = create_displacement_object(preview_core)

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[scene.mt_scene_props.mt_tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

    textured_vertex_groups = ['Top']

    # create a vertex group for the displacement modifier
    mod_vert_group_name = construct_displacement_mod_vert_group(displacement_core, textured_vertex_groups)

    assign_displacement_materials(
        displacement_core,
        [image_size, image_size],
        primary_material,
        secondary_material,
        vert_group=mod_vert_group_name)

    assign_preview_materials(preview_core, primary_material, secondary_material, textured_vertex_groups)

    preview_core.mt_object_props.geometry_type = 'PREVIEW'
    displacement_core.mt_object_props.geometry_type = 'DISPLACEMENT'

    return preview_core, displacement_core


def create_openlock_base(tile_props):
    '''Creates an openlock style base'''
    tile_props.base_size = Vector((
        tile_props.tile_size[0],
        tile_props.tile_size[1],
        .2756))


    if tile_props.base_size[0] >= 1 and tile_props.base_size[1] < 1 and tile_props.base_size[1] > 0.496:
        # if base is less than an inch wide use a wall type base
        base = create_openlock_wall_base(tile_props)

    else:
        base = draw_openlock_rect_floor_base(tile_props.base_size)
        base.name = tile_props.tile_name + '.base'
        add_object_to_collection(base, tile_props.tile_name)
        clip_cutters = create_openlock_base_clip_cutter(base, tile_props)

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

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    return base


def create_openlock_base_clip_cutter(base, tile_props):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- base the cutter will be used on
    tile_name -- the tile name
    """
    mode('OBJECT')

    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_props.tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    # get location of bottom front left corner of tile
    front_left = Vector((
        base_location[0] - (tile_props.base_size[0] / 2),
        base_location[1] - (tile_props.base_size[1] / 2),
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
    array_mod.fit_length = tile_props.base_size[0] - 1

    select(clip_cutter.name)
    activate(clip_cutter.name)
    mirror_mod = clip_cutter.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = False
    mirror_mod.use_axis[1] = True
    mirror_mod.mirror_object = base

    clip_cutter2 = clip_cutter.copy()
    clip_cutter2.data = clip_cutter2.data.copy()

    add_object_to_collection(clip_cutter2, tile_props.tile_name)
    clip_cutter2.rotation_euler = (0, 0, math.radians(90))

    front_right = Vector((
        base_location[0] + (tile_props.base_size[0] / 2),
        base_location[1] - (tile_props.base_size[1] / 2),
        base_location[2]))

    clip_cutter2.location = (
        front_right[0] - 0.25,
        front_right[1] + 0.5,
        front_right[2])

    array_mod2 = clip_cutter2.modifiers['Array']
    array_mod2.fit_type = 'FIT_LENGTH'
    array_mod2.fit_length = tile_props.base_size[1] - 1
    mirror_mod2 = clip_cutter2.modifiers['Mirror']
    mirror_mod2.use_axis[0] = True
    mirror_mod2.use_axis[1] = False

    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

    return [clip_cutter, clip_cutter2]
