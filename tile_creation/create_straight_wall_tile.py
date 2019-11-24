""" Contains functions for creating wall tiles """
import os
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_path
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import deselect_all, select_all, select, activate
from .. lib.utils.utils import mode
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import load_secondary_material, load_material, assign_mat_to_vert_group, add_displacement_mesh_modifiers, assign_displacement_materials, assign_preview_materials
from .. enums.enums import geometry_types


def create_straight_wall(
        tile_blueprint,
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        tile_material):

    """Returns a straight wall
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
        base_size = Vector((tile_size[0], 0.5, 0.2755))
        base = create_openlock_straight_wall_base(tile_name, base_size)

    if base_system == 'PLAIN':
        base = create_straight_wall_base(tile_name, base_size)

    if tile_system == 'OPENLOCK':
        tile_size = Vector((tile_size[0], 0.3149, tile_size[2]))
        create_openlock_wall(tile_name, tile_size, base_size, tile_material)

    if tile_system == 'PLAIN':
        create_plain_wall(tile_name, tile_size, base_size, tile_material)


def create_wall_slabs(tile_name, core_size, base_size, tile_size, tile_material):
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

    primary_material = load_material(tile_material)
    secondary_material = load_secondary_material()

    #image_size = bpy.context.scene.mt_tile_resolution
    #print(image_size)
    assign_displacement_materials(inner_displacement_slab, 'Y', 'y_neg', 'neg', [2048, 2048], primary_material)
    assign_preview_materials(inner_preview_slab, 'y_neg', primary_material, secondary_material)

    assign_displacement_materials(outer_displacement_slab, 'Y', 'y_pos', 'pos', [2048, 2048], primary_material)
    assign_preview_materials(outer_preview_slab, 'y_pos', primary_material, secondary_material)
    # hide final slabs for now
    outer_displacement_slab.hide_viewport = True
    inner_displacement_slab.hide_viewport = True


def create_openlock_wall(tile_name, tile_size, base_size, tile_material):
    core = create_openlock_straight_wall_core(tile_name, tile_size, base_size)
    create_wall_slabs(tile_name, core.dimensions, base_size, tile_size, tile_material)


def create_plain_wall(tile_name, tile_size, base_size, tile_material):
    core_size = Vector((tile_size[0], tile_size[1] - 0.1850, tile_size[2]))
    core = create_straight_wall_core(tile_name, core_size, base_size)
    create_wall_slabs(tile_name, core.dimensions, base_size, tile_size, tile_material)


def create_straight_wall_core(
        tile_name,
        tile_size,
        base_size):
    '''Returns the core (vertical inner) part of a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
    mode('OBJECT')

    # make our core
    core = draw_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    mode('OBJECT')
    select(core.name)
    activate(core.name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (-tile_size[0] / 2, -tile_size[1] / 2, base_size[2])
    bpy.context.scene.cursor.location = [0, 0, 0]
    select(core.name)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    core['geometry_type'] = 'CORE'

    return core


def create_preview_slab(
        tile_name,
        core_size,
        base_size):
    slab_size = Vector((core_size[0], 0.0925, core_size[2]))
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

    cursor_start_location = bpy.context.scene.cursor.location.copy()

    if geometry_type == 'PREVIEW':
        slab = create_preview_slab(tile_name, core_size, base_size)
    else:
        slab = create_displacement_slab(tile_name, core_size, base_size)

    slab['geometry_type'] = geometry_type

    if slab_type == 'inner':
        slab.location = (-core_size[0] / 2, -core_size[1] / 2 - slab.dimensions[1], base_size[2])
    else:
        slab.location = (-core_size[0] / 2, core_size[1] / 2, base_size[2])

    bpy.context.scene.cursor.location = [0, 0, 0]
    mode('OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    slab.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location

    select(slab.name)
    activate(slab.name)
    bpy.ops.uv.smart_project()
    cuboid_sides_to_vert_groups(slab)

    return slab


def create_straight_wall_base(
        tile_name,
        base_size):
    """Returns a base for a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain,
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z]
    """

    # make base

    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    mode('OBJECT')
    select(base.name)
    activate(base.name)

    # move base so centred and set origin to world origin
    base.location = (- base_size[0] / 2, - base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    base['geometry_type'] = 'BASE'
    return base


def create_openlock_straight_wall_base(tile_name, base_size):
    """takes a straight wall base and makes it into an openlock style base"""
    # make base
    base = create_straight_wall_base(tile_name, base_size)

    slot_cutter = create_openlock_base_slot_cutter(base, tile_name)
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
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
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

    return core


def create_openlock_wall_cutters(slab, tile_size, tile_name):
    """Creates the cutters for the wall and positions them correctly

    Keyword arguments:
    slab -- wall slab object
    tile_size --0 [x, y, z] Size of tile including any base but excluding any
    positive booleans
    """
    deselect_all()

    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    side_cutter1 = data_to.objects[0]
    add_object_to_collection(side_cutter1, tile_name)

    slab_location = slab.location

    # get location of bottom front left corner of tile
    front_left = [
        slab_location[0] - (tile_size[0] / 2),
        slab_location[1] - (tile_size[1] / 2),
        0]
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
    array_mod.fit_length = tile_size[2] - 0.10236

    mirror_mod = side_cutter1.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = True
    mirror_mod.mirror_object = slab

    # make a copy of side cutter 1
    side_cutter2 = side_cutter1.copy()

    add_object_to_collection(side_cutter2, tile_name)

    # move cutter up by 0.75 inches
    side_cutter2.location[2] = side_cutter2.location[2] + 0.75

    array_mod = side_cutter2.modifiers["Array"]
    array_mod.fit_length = tile_size[2] - 0.18110

    return [side_cutter1, side_cutter2]


def create_openlock_base_clip_cutter(base, tile_name):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    object -- base the cutter will be used on
    """

    mode('OBJECT')
    base_size = base.dimensions

    # get original location of base and cursor
    base_location = base.location.copy()

    # Get cutter
    deselect_all()
    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")

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
    # get location of bottom front left corner of tile
    front_left = [
        base_location[0] - (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        0]

    # move cutter to starting point
    clip_cutter.location = [
        front_left[0] + 0.5,
        front_left[1] + 0.25,
        front_left[2]]

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base_size[0] - 1

    return (clip_cutter)


def create_openlock_base_slot_cutter(base, tile_name):
    """Makes a cutter for the openlock base slot
    based on the width of the base

    Keyword arguments:
    object -- base the cutter will be used on
    """
    cursor = bpy.context.scene.cursor
    mode('OBJECT')
    base_dim = base.dimensions

    # get original location of object and cursor
    base_loc = base.location.copy()
    cursor_original_loc = cursor.location.copy()

    # move cursor to origin
    cursor.location = [0, 0, 0]

    # work out bool size X from base size, y and z are constants
    bool_size = [
        base_dim[0] - (0.236 * 2),
        0.197,
        0.25]

    cutter_mesh = bpy.data.meshes.new("cutter_mesh")
    cutter = bpy.data.objects.new(tile_name + ".cutter.slot", cutter_mesh)
    add_object_to_collection(cutter, tile_name)
    select(cutter.name)
    activate(cutter.name)

    cutter = draw_cuboid(bool_size)
    mode('OBJECT')

    # move cutter so centred and set cutter origin to world origin + z = -0.001
    # (to avoid z fighting)
    cutter.location = (-bool_size[0] / 2, -0.014, 0)
    cursor.location = [0.0, 0.0, 0.001]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    # reset cursor location
    cursor.location = cursor_original_loc

    # set cutter location to base origin
    cutter.location = base_loc

    return (cutter)
