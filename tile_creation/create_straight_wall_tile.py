""" Contains functions for creating wall tiles """
import os
from math import radians
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.utils import mode, apply_all_modifiers
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    assign_displacement_materials_2,
    assign_preview_materials_2)
from .. operators.trim_tile import (
    create_tile_trimmers)


def create_straight_wall(tile_empty):
    """Returns a straight wall
    Keyword arguments:
    tile_empty -- EMPTY, empty which the tile is parented to. \
        Stores properties that relate to the entire tile
    """

    tile_properties = tile_empty['tile_properties']
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_size'] = Vector((tile_properties['tile_size'][0], 0.5, 0.2755))
        base = create_openlock_straight_wall_base(tile_properties)

    if tile_properties['base_blueprint'] == 'PLAIN':
        base = create_straight_wall_base(tile_properties)

    if tile_properties['base_blueprint'] == 'NONE':
        base = bpy.data.objects.new(tile_properties['tile_name'] + '.base', None)
        tile_properties['base_size'] = (0, 0, 0)
        add_object_to_collection(base, tile_properties['tile_name'])

    if tile_properties['main_part_blueprint'] == 'OPENLOCK':
        tile_properties['tile_size'] = Vector((tile_properties['tile_size'][0], 0.3149, tile_properties['tile_size'][2]))
        create_openlock_wall_2(tile_properties, base)

    if tile_properties['main_part_blueprint'] == 'PLAIN':
        create_plain_wall_2(tile_properties, base)

    # create tile trimmers. Used to ensure that displaced
    # textures don't extend beyond the original bounds of the tile.
    # Used by voxeliser and exporter
    tile_properties['trimmers'] = create_tile_trimmers(tile_properties)

    base.parent = tile_empty
    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc
    tile_empty['tile_properties'] = tile_properties


def create_openlock_wall_2(tile_properties, base):
    tile_properties['base_size'] = base.dimensions
    textured_faces = tile_properties['textured_faces']

    preview_core, displacement_core = create_openlock_straight_wall_core_2(tile_properties)

    preview_core['geometry_type'] = 'PREVIEW'
    displacement_core['geometry_type'] = 'DISPLACEMENT'

    preview_core['displacement_obj'] = displacement_core
    displacement_core['preview_obj'] = preview_core

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_properties['tile_materials']['tile_material_1']]

    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials_2(displacement_core, [image_size, image_size], primary_material, secondary_material, textured_faces)
    assign_preview_materials_2(preview_core, primary_material, secondary_material, textured_faces)

    # create wall cutters

    cores = [preview_core, displacement_core]

    if tile_properties['tile_size'][2] >= 0.99:
        textured_faces = tile_properties['textured_faces']
        if textured_faces['x_neg'] is 0 or textured_faces['x_pos'] is 0:
            wall_cutters = create_openlock_wall_cutters_2(preview_core, tile_properties)

            for wall_cutter in wall_cutters:
                wall_cutter.parent = base
                wall_cutter.display_type = 'BOUNDS'
                wall_cutter.hide_viewport = True

                for core in cores:
                    wall_cutter_bool = core.modifiers.new('Wall Cutter', 'BOOLEAN')
                    wall_cutter_bool.operation = 'DIFFERENCE'
                    wall_cutter_bool.object = wall_cutter

    displacement_core.hide_viewport = True


def create_plain_wall_2(tile_properties, base):
    tile_properties['base_size'] = base.dimensions
    textured_faces = tile_properties['textured_faces']

    preview_core = create_straight_wall_core_2(tile_properties)
    preview_core['geometry_type'] = 'PREVIEW'

    displacement_core = create_straight_wall_core_2(tile_properties)
    displacement_core['geometry_type'] = 'DISPLACEMENT'

    preview_core['displacement_obj'] = displacement_core
    displacement_core['preview_obj'] = preview_core

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_properties['tile_materials']['tile_material_1']]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials_2(displacement_core, [image_size, image_size], primary_material, secondary_material, textured_faces)
    assign_preview_materials_2(preview_core, primary_material, secondary_material, textured_faces)

    displacement_core.hide_viewport = True


def create_straight_wall_core_2(
        tile_properties):
    '''Returns the core (vertical) part of a wall tile
    '''
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    deselect_all()

    # make our core
    core = draw_cuboid([
        tile_properties['tile_size'][0],
        tile_properties['tile_size'][1],
        tile_properties['tile_size'][2] - tile_properties['base_size'][2]])

    core.name = tile_properties['tile_name'] + '.core'
    add_object_to_collection(core, tile_properties['tile_name'])
    core_location = core.location.copy()
    mode('OBJECT')

    # move core so centred, move up so on top of base and set origin to world origin

    core.location = (core_location[0] - tile_properties['tile_size'][0] / 2, core_location[1] - tile_properties['tile_size'][1] / 2, core_location[2] + tile_properties['base_size'][2])
    cursor.location = cursor_start_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.uv.smart_project()
    cuboid_sides_to_vert_groups(core)

    return core


def create_straight_wall_base(
        tile_properties):
    """Returns a base for a wall tile

    Keyword arguments:
    tile_properties['tile_name']   -- STR, name,
    tile_properties['base_size']   -- VECTOR, [x, y, z]
    """
    cursor = bpy.context.scene.cursor
    cursor_start_location = cursor.location.copy()

    # make base
    base = draw_cuboid(tile_properties['base_size'])
    base.name = tile_properties['tile_name'] + '.base'
    add_object_to_collection(base, tile_properties['tile_name'])
    base_location = base.location.copy()

    mode('OBJECT')
    select(base.name)
    activate(base.name)

    base.location = (base_location[0] - tile_properties['base_size'][0] / 2, base_location[1] + tile_properties['base_size'][1] / 2, base_location[2] + tile_properties['base_size'][2])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    base.location = cursor_start_location
    bpy.context.scene.cursor.location = cursor_start_location
    base['geometry_type'] = 'BASE'

    return base


def create_openlock_straight_wall_base(tile_properties):
    """takes a straight wall base and makes it into an openlock style base"""
    # make base
    base = create_straight_wall_base(tile_properties)

    slot_cutter = create_openlock_base_slot_cutter(base, tile_properties)

    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'
    slot_cutter.hide_viewport = True

    clip_cutter = create_openlock_base_clip_cutter(base, tile_properties)
    clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
    clip_boolean.operation = 'DIFFERENCE'
    clip_boolean.object = clip_cutter
    clip_cutter.parent = base
    clip_cutter.display_type = 'BOUNDS'
    clip_cutter.hide_viewport = True

    return base


def create_openlock_straight_wall_core_2(
        tile_properties):

    preview_core = create_straight_wall_core_2(tile_properties)
    displacement_core = create_straight_wall_core_2(tile_properties)

    return preview_core, displacement_core


def create_openlock_wall_cutters_2(core, tile_properties):
    """Creates the cutters for the wall and positions them correctly

    Keyword arguments:
    core -- OBJ, wall core object
    tile_properties['tile_size'] -- VECTOR [x, y, z] Size of tile including any base
    tile_properties['tile_name'] -- STR, tile name
    """
    textured_faces = tile_properties['textured_faces']
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    core_location = core.location

    cutters = []
    # left side cutters
    if textured_faces['x_neg'] is 0:
        left_cutter_bottom = data_to.objects[0].copy()
        add_object_to_collection(left_cutter_bottom, tile_properties['tile_name'])
        # get location of bottom front left corner of tile
        front_left = [
            core_location[0] - (tile_properties['tile_size'][0] / 2),
            core_location[1] - (tile_properties['tile_size'][1] / 2),
            core_location[2]]
        # move cutter to bottom front left corner then up by 0.63 inches
        left_cutter_bottom.location = [
            front_left[0],
            front_left[1] + (tile_properties['tile_size'][1] / 2),
            front_left[2] + 0.63]

        array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
        array_mod.use_relative_offset = False
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace[2] = 2
        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_properties['tile_size'][2] - 1

        # make a copy of left cutter bottom
        left_cutter_top = left_cutter_bottom.copy()

        add_object_to_collection(left_cutter_top, tile_properties['tile_name'])

        # move cutter up by 0.75 inches
        left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

        array_mod = left_cutter_top.modifiers[array_mod.name]
        array_mod.fit_length = tile_properties['tile_size'][2] - 1.8

        cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters
    if textured_faces['x_pos'] is 0:
        right_cutter_bottom = data_to.objects[0].copy()
        add_object_to_collection(right_cutter_bottom, tile_properties['tile_name'])
        # get location of bottom front right corner of tile
        front_right = [
            core_location[0] + (tile_properties['tile_size'][0] / 2),
            core_location[1] - (tile_properties['tile_size'][1] / 2),
            core_location[2]]
        # move cutter to bottom front left corner then up by 0.63 inches
        right_cutter_bottom.location = [
            front_right[0],
            front_right[1] + (tile_properties['tile_size'][1] / 2),
            front_right[2] + 0.63]
        # rotate cutter 180 degrees around Z
        right_cutter_bottom.rotation_euler[2] = radians(180)

        array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
        array_mod.use_relative_offset = False
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace[2] = 2
        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_properties['tile_size'][2] - 1

        right_cutter_top = right_cutter_bottom.copy()
        add_object_to_collection(right_cutter_top, tile_properties['tile_name'])
        right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

        array_mod = right_cutter_top.modifiers["Array"]
        array_mod.fit_length = tile_properties['tile_size'][2] - 1.8

        cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters


def create_openlock_base_clip_cutter(base, tile_properties):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- OBJ, base the cutter will be used on
    tile_properties['tile_name'] -- STR, tilename
    """

    mode('OBJECT')
    tile_properties['base_size'] = base.dimensions

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
        add_object_to_collection(obj, tile_properties['tile_name'])

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    clip_cutter.location = Vector((
        base_location[0] - (tile_properties['base_size'][0] / 2) + 0.5,
        base_location[1] - (tile_properties['base_size'][1] / 2) + 0.25,
        base_location[2]))

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_properties['base_size'][0] - 1

    return (clip_cutter)


def create_openlock_base_slot_cutter(base, tile_properties, offset=0.18):
    """Makes a cutter for the openlock base slot
    based on the width of the base

    Keyword arguments:
    base -- OBJ, base the cutter will be used on
    tile_properties['tile_name'] -- STR
    """
    cursor = bpy.context.scene.cursor
    mode('OBJECT')
    base_dimensions = base.dimensions

    # get original location of object and cursor
    base_location = base.location.copy()
    cursor_original_location = cursor.location.copy()

    # work out bool size X from base size, y and z are constants
    bool_size = [
        tile_properties['base_size'][0] - (0.236 * 2),
        0.197,
        0.25]

    cutter_mesh = bpy.data.meshes.new("cutter_mesh")
    cutter = bpy.data.objects.new(tile_properties['tile_name'] + ".cutter.slot", cutter_mesh)
    add_object_to_collection(cutter, tile_properties['tile_name'])
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
