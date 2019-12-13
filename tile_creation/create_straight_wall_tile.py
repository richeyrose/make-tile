""" Contains functions for creating wall tiles """
import os
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_path, get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.utils import mode
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    add_displacement_mesh_modifiers,
    add_preview_mesh_modifiers,
    assign_displacement_materials,
    assign_preview_materials,
    assign_displacement_materials_2,
    assign_preview_materials_2)
from .. enums.enums import geometry_types


def create_straight_wall(
        tile_blueprint,
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        tile_material,
        textured_faces):

    """Returns a straight wall
    Keyword arguments:
    tile_blueprint -- STR, a blueprint consists of a tile type and base type
    tile_system -- STR, tile system for slabs
    tile_name   -- STR, name,
    tile_size   -- VECTOR [x, y, z],
    base_size   -- VECTOR [x, y, z],
    base_system -- STR tile system for bases
    tile_material -- STR material name
    """
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    if base_system == 'OPENLOCK':
        base_size = Vector((tile_size[0], 0.5, 0.2755))
        base = create_openlock_straight_wall_base(tile_name, base_size)

    if base_system == 'PLAIN':
        base = create_straight_wall_base(tile_name, base_size)

    if tile_system == 'OPENLOCK':
        tile_size = Vector((tile_size[0], 0.3149, tile_size[2]))
        create_openlock_wall(tile_name, tile_size, base, tile_material)

    if tile_system == 'PLAIN':
        # create_plain_wall(tile_name, tile_size, base, tile_material)
        create_plain_wall_2(tile_name, tile_size, base, tile_material, textured_faces)

    base.location = cursor_orig_loc
    cursor.location = cursor_orig_loc


def create_wall_slabs(displacement_type, tile_name, core_size, base_size, tile_size, tile_material):
    """Returns a list of slabs
    Keyword arguments:
    displacement_type -- STR - whether to use an 'AXIS' or 'NORMAL' for material displacement
    tile_name   -- STR, name,
    core_size -- VECTOR [x, y, z]
    base_sized -- VECTOR [x, y, z]
    tile_size -- VECTOR [x, y, z]
    tile_material -- STR material name
    """

    outer_preview_slab = create_straight_wall_slab(
        tile_name,
        core_size,
        base_size,
        'outer',
        'PREVIEW')
    outer_preview_slab['geometry_type'] = 'PREVIEW'

    outer_displacement_slab = create_straight_wall_slab(
        tile_name,
        core_size,
        base_size,
        'outer',
        'DISPLACEMENT')
    outer_displacement_slab['geometry_type'] = 'DISPLACEMENT'

    outer_preview_slab['displacement_obj'] = outer_displacement_slab
    outer_displacement_slab['preview_obj'] = outer_preview_slab

    inner_preview_slab = create_straight_wall_slab(
        tile_name,
        core_size,
        base_size,
        'inner',
        'PREVIEW')
    inner_preview_slab['geometry_type'] = 'PREVIEW'

    inner_displacement_slab = create_straight_wall_slab(
        tile_name,
        core_size,
        base_size,
        'inner',
        'DISPLACEMENT')
    inner_displacement_slab['geometry_type'] = 'DISPLACEMENT'

    inner_preview_slab['displacement_obj'] = inner_displacement_slab
    inner_displacement_slab['preview_obj'] = inner_preview_slab

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_material]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    if displacement_type is not 'NORMAL':
        assign_displacement_materials(inner_displacement_slab, 'Y', 'y_neg', 'neg', [image_size, image_size], primary_material)
        assign_displacement_materials(outer_displacement_slab, 'Y', 'y_pos', 'pos', [image_size, image_size], primary_material)

    else:
        assign_displacement_materials(inner_displacement_slab, 'NORMAL', 'y_neg', 'pos', [image_size, image_size], primary_material)
        assign_displacement_materials(outer_displacement_slab, 'NORMAL', 'y_pos', 'pos', [image_size, image_size], primary_material)

    assign_preview_materials(inner_preview_slab, 'y_neg', primary_material, secondary_material)
    assign_preview_materials(outer_preview_slab, 'y_pos', primary_material, secondary_material)

    # hide final slabs for now

    outer_displacement_slab.hide_viewport = True
    inner_displacement_slab.hide_viewport = True

    slabs = [outer_preview_slab, outer_displacement_slab, inner_preview_slab, inner_displacement_slab]
    return slabs


def create_openlock_wall(tile_name, tile_size, base, tile_material):
    displacement_type = 'AXIS'
    base_size = base.dimensions

    core, wall_cutters = create_openlock_straight_wall_core(tile_name, tile_size, base_size)

    core.parent = base

    slabs = create_wall_slabs(displacement_type, tile_name, core.dimensions, base_size, tile_size, tile_material)

    for slab in slabs:
        slab.parent = base


def create_plain_wall(tile_name, tile_size, base, tile_material):
    base_size = base.dimensions
    core_size = Vector((tile_size[0], tile_size[1] - 0.1850, tile_size[2]))
    core = create_straight_wall_core(tile_name, core_size, base_size)
    core.parent = base
    slabs = create_wall_slabs(tile_name, core.dimensions, base_size, tile_size, tile_material)
    for slab in slabs:
        slab.parent = base


def create_plain_wall_2(tile_name, tile_size, base, tile_material, textured_faces):
    base_size = base.dimensions
    core_size = Vector((tile_size))

    preview_core = create_straight_wall_core_2(tile_name, core_size, base_size)
    preview_core['geometry_type'] = 'PREVIEW'

    displacement_core = create_straight_wall_core_2(tile_name, core_size, base_size)
    displacement_core['geometry_type'] = 'DISPLACEMENT'

    preview_core['displacement_obj'] = displacement_core
    displacement_core['preview_obj'] = preview_core

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_material]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials_2(displacement_core, [image_size, image_size], primary_material, secondary_material, textured_faces)
    assign_preview_materials_2(preview_core, primary_material, secondary_material, textured_faces)

    displacement_core.hide_viewport = True


def create_straight_wall_core_2(
        tile_name,
        tile_size,
        base_size):
    '''Returns the core (vertical inner) part of a wall tile

    Keyword arguments:
    tile_name   -- STR, name
    tile_size   -- VECTOR, [x, y, z]
    base_size   -- VECTOR, [x, y, z]
    '''
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    deselect_all()

    # make our core
    core = draw_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)
    core_location = core.location.copy()
    mode('OBJECT')

    # move core so centred, move up so on top of base and set origin to world origin

    core.location = (core_location[0] - tile_size[0] / 2, core_location[1] - tile_size[1] / 2, core_location[2] + base_size[2])
    cursor.location = cursor_start_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.uv.smart_project()
    cuboid_sides_to_vert_groups(core)

    return core


def create_straight_wall_core(
        tile_name,
        tile_size,
        base_size):
    '''Returns the core (vertical inner) part of a wall tile

    Keyword arguments:
    tile_name   -- STR, name
    tile_size   -- VECTOR, [x, y, z]
    base_size   -- VECTOR, [x, y, z]
    '''
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    deselect_all()

    # make our core
    core = draw_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)
    core_location = core.location.copy()
    mode('OBJECT')

    # move core so centred, move up so on top of base and set origin to world origin

    core.location = (core_location[0] - tile_size[0] / 2, core_location[1] - tile_size[1] / 2, core_location[2] + base_size[2])
    cursor.location = cursor_start_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    core['geometry_type'] = 'CORE'

    return core


def create_preview_slab(
        tile_name,
        core_size,
        base_size):
    slab_size = Vector((core_size[0], 0.0039, core_size[2]))
    slab = draw_cuboid(slab_size)
    slab.name = tile_name + '.slab.preview'
    add_object_to_collection(slab, tile_name)
    return slab


def create_displacement_slab(
        tile_name,
        core_size,
        base_size):
    slab_size = Vector((core_size[0], 0.0039, core_size[2]))
    slab = draw_cuboid(slab_size)
    slab.name = tile_name + '.slab.displacement'
    add_object_to_collection(slab, tile_name)
    return slab


def create_straight_wall_slab(
        tile_name,
        core_size,
        base_size,
        slab_type,
        geometry_type):

    deselect_all()
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    if geometry_type == 'PREVIEW':
        slab = create_preview_slab(tile_name, core_size, base_size)
    else:
        slab = create_displacement_slab(tile_name, core_size, base_size)

    mode('OBJECT')

    slab_location = slab.location.copy()
    slab['geometry_type'] = geometry_type

    if slab_type == 'inner':
        slab.location = (slab_location[0] - core_size[0] / 2, slab_location[1] - core_size[1] / 2 - slab.dimensions[1], slab_location[2] + base_size[2])

    else:
        slab.location = (slab_location[0] - core_size[0] / 2, slab_location[1] + core_size[1] / 2, slab_location[2] + base_size[2])

    cursor.location = (cursor_start_location[0], cursor_start_location[1], cursor_start_location[2] + base_size[2])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.uv.smart_project()
    cuboid_sides_to_vert_groups(slab)

    bpy.context.scene.cursor.location = cursor_start_location

    return slab


def create_straight_wall_base(
        tile_name,
        base_size):
    """Returns a base for a wall tile

    Keyword arguments:
    tile_name   -- STR, name,
    base_size   -- VECTOR, [x, y, z]
    """
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    # make base
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)
    base_location = base.location.copy()

    mode('OBJECT')
    select(base.name)
    activate(base.name)

    base.location = (base_location[0] - base_size[0] / 2, base_location[1] + base_size[1] / 2, base_location[2] + base_size[2])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    base.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location
    base['geometry_type'] = 'BASE'

    return base


def create_openlock_straight_wall_base(tile_name, base_size):
    """takes a straight wall base and makes it into an openlock style base"""
    # make base
    base = create_straight_wall_base(tile_name, base_size)

    slot_cutter = create_openlock_base_slot_cutter(base, base_size, tile_name)

    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'
    slot_cutter.hide_viewport = True

    clip_cutter = create_openlock_base_clip_cutter(base, tile_name)
    clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
    clip_boolean.operation = 'DIFFERENCE'
    clip_boolean.object = clip_cutter
    clip_cutter.parent = base
    clip_cutter.display_type = 'BOUNDS'
    clip_cutter.hide_viewport = True

    return base


def create_openlock_straight_wall_core(
        tile_name,
        tile_size,
        base_size):
    '''Returns the core (vertical inner) part of a wall tile

    Keyword arguments:
    tile_name   -- STR, name
    tile_size   -- VECTOR, [x, y, z]
    base_size   -- VECTOR, [x, y, z]
    '''

    core = create_straight_wall_core(tile_name, tile_size, base_size)

    # check to see if tile is at least 1 inch high
    if tile_size[2] >= 0.99:
        wall_cutters = create_openlock_wall_cutters(core, tile_size, tile_name)
        for wall_cutter in wall_cutters:
            wall_cutter.parent = core
            wall_cutter.display_type = 'BOUNDS'
            wall_cutter.hide_viewport = True
            wall_cutter_bool = core.modifiers.new('Wall Cutter', 'BOOLEAN')
            wall_cutter_bool.operation = 'DIFFERENCE'
            wall_cutter_bool.object = wall_cutter

    return core, wall_cutters


def create_openlock_wall_cutters(core, tile_size, tile_name):
    """Creates the cutters for the wall and positions them correctly

    Keyword arguments:
    core -- OBJ, wall core object
    tile_size -- VECTOR [x, y, z] Size of tile including any base
    tile_name -- STR, tile name
    """
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    side_cutter1 = data_to.objects[0]
    add_object_to_collection(side_cutter1, tile_name)

    core_location = core.location

    # get location of bottom front left corner of tile
    front_left = [
        core_location[0] - (tile_size[0] / 2),
        core_location[1] - (tile_size[1] / 2),
        core_location[2]]
    # move cutter to bottom front left corner then up by 0.63 inches
    side_cutter1.location = [
        front_left[0],
        front_left[1] + (tile_size[1] / 2),
        front_left[2] + 0.63]

    array_mod = side_cutter1.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    mirror_mod = side_cutter1.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = True
    mirror_mod.mirror_object = core

    # make a copy of side cutter 1
    side_cutter2 = side_cutter1.copy()

    add_object_to_collection(side_cutter2, tile_name)

    # move cutter up by 0.75 inches
    side_cutter2.location[2] = side_cutter2.location[2] + 0.75

    array_mod = side_cutter2.modifiers["Array"]
    array_mod.fit_length = tile_size[2] - 1.8

    return [side_cutter1, side_cutter2]


def create_openlock_base_clip_cutter(base, tile_name):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- OBJ, base the cutter will be used on
    tile_name -- STR, tilename
    """

    mode('OBJECT')
    base_size = base.dimensions

    # get original location of cursor
    cursor_original_location = bpy.context.scene.cursor.location.copy()
    base_location = base.location.copy()
    # Get cutter
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load base cutters
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    clip_cutter.location = Vector((
        base_location[0] - (base_size[0] / 2) + 0.5,
        base_location[1] - (base_size[1] / 2) + 0.25,
        base_location[2]))

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base_size[0] - 1

    return (clip_cutter)


def create_openlock_base_slot_cutter(base, base_size, tile_name, offset=0.18):
    """Makes a cutter for the openlock base slot
    based on the width of the base

    Keyword arguments:
    base -- OBJ, base the cutter will be used on
    tile_name -- STR
    """
    cursor = bpy.context.scene.cursor
    mode('OBJECT')
    base_dimensions = base.dimensions

    # get original location of object and cursor
    base_location = base.location.copy()
    cursor_original_location = cursor.location.copy()

    # work out bool size X from base size, y and z are constants
    bool_size = [
        base_size[0] - (0.236 * 2),
        0.197,
        0.25]

    cutter_mesh = bpy.data.meshes.new("cutter_mesh")
    cutter = bpy.data.objects.new(tile_name + ".cutter.slot", cutter_mesh)
    add_object_to_collection(cutter, tile_name)
    cutter = draw_cuboid(bool_size)

    mode('OBJECT')
    deselect_all()
    select(cutter.name)
    activate(cutter.name)

    cutter.location = (base_location[0] - bool_size[0] / 2, base_location[1] + offset, base_location[2] + cutter.dimensions[2] - 0.001)

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    # reset cursor location
    cursor.location = cursor_original_location

    # set cutter location to base origin
    cutter.location = base_location

    return (cutter)
