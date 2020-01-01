import os
import bpy
from mathutils import Vector
from math import degrees, radians, pi, modf
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_path, get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.utils import mode, view3d_find, add_circle_array, add_deform_modifiers
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    assign_displacement_materials,
    assign_preview_materials)
from .. enums.enums import geometry_types
from . create_straight_wall_tile import (
    create_plain_base as create_plain_straight_wall_base,
    create_wall_cores as create_straight_wall_cores,
    create_core,
    create_openlock_base_slot_cutter)
from .. operators.trim_tile import (
    create_curved_wall_tile_trimmers)


def create_curved_wall(tile_empty):
    """Returns a curved wall"""

    tile_properties = tile_empty['tile_properties']

    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_inner_radius'] = tile_properties['wall_inner_radius'] + (tile_properties['base_size'][1] / 2)
        tile_properties['base_size'] = Vector((tile_properties['tile_size'][0], 0.5, 0.2755))
        base = create_openlock_base(tile_properties)

    if tile_properties['base_blueprint'] == 'PLAIN':
        tile_properties['base_inner_radius'] = tile_properties['base_inner_radius'] + (tile_properties['base_size'][1] / 2)
        base = create_plain_base(tile_properties)

    if tile_properties['main_part_blueprint'] == 'OPENLOCK':
        tile_properties['tile_size'] = Vector((tile_properties['tile_size'][0], 0.5, tile_properties['tile_size'][2]))
        preview_core, displacement_core = create_openlock_cores(base, tile_properties, tile_empty)

    if tile_properties['main_part_blueprint'] == 'PLAIN':
        preview_core, displacement_core = create_wall_cores(base, tile_properties)
        displacement_core.hide_viewport = True
    # create tile trimmers. Used to ensure that displaced
    # textures don't extend beyond the original bounds of the tile.
    # Used by voxeliser and exporter

    tile_properties['trimmers'] = create_curved_wall_tile_trimmers(tile_properties)

    base.parent = tile_empty
    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc
    tile_empty['tile_properties'] = tile_properties


def create_plain_base(tile_properties):

    circumference = 2 * pi * tile_properties['base_inner_radius']
    base_length = circumference / (360 / tile_properties['degrees_of_arc'])
    tile_properties['base_size'] = Vector((base_length, tile_properties['base_size'][1], tile_properties['base_size'][2]))

    base = create_plain_straight_wall_base(tile_properties)
    add_deform_modifiers(base, tile_properties['segments'], tile_properties['degrees_of_arc'])

    return base


def create_openlock_base(tile_properties):
    base = create_plain_base(tile_properties)

    # make base slot
    if tile_properties['base_socket_sides'] == 'INNER':
        slot_cutter = create_openlock_base_slot_cutter(base, tile_properties, offset=0.017)
    else:
        slot_cutter = create_openlock_base_slot_cutter(base, tile_properties['base_size'], tile_properties['tile_name'])

    add_deform_modifiers(slot_cutter, tile_properties['segments'], tile_properties['degrees_of_arc'])
    slot_cutter.hide_viewport = True

    clip_cutter = create_openlock_base_clip_cutter(base, tile_properties)

    return base


def create_openlock_base_clip_cutter(base, tile_properties):
    # load base cutter
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    clip_cutter = data_to.objects[0]
    add_object_to_collection(clip_cutter, tile_properties['tile_name'])

    deselect_all()
    select(clip_cutter.name)

    if tile_properties['base_socket_sides'] == 'INNER':
        bpy.ops.transform.rotate(value=radians(180), orient_axis='Z')
        bpy.ops.object.transform_apply(location=False, scale=False, properties=False)

    loc = clip_cutter.location
    circle_center = Vector((loc[0], loc[1] + tile_properties['base_inner_radius'], loc[2]))

    bpy.ops.transform.rotate(value=radians((tile_properties['degrees_of_arc'] / 2) - 22.5), orient_axis='Z', center_override=circle_center)
    bpy.ops.object.transform_apply(location=False, scale=False, properties=False)
    num_cutters = modf((tile_properties['degrees_of_arc'] - 22.5) / 22.5)
    array_name, empty = add_circle_array(clip_cutter, circle_center, num_cutters[1], 'Z', tile_properties['degrees_of_arc'] - 22.5)
    empty.parent = base
    empty.hide_viewport = True

    clip_cutter.parent = base
    clip_cutter.display_type = 'BOUNDS'
    clip_cutter.hide_viewport = True
    clip_cutter_bool = base.modifiers.new('Base Cutter', 'BOOLEAN')
    clip_cutter_bool.operation = 'DIFFERENCE'
    clip_cutter_bool.object = clip_cutter

    return clip_cutter


def create_wall_cores(base, tile_properties):
    # calculate wall dimensions
    tile_properties['wall_inner_radius'] = (
        tile_properties['wall_inner_radius'] + (tile_properties['tile_size'][1] / 2))

    circumference = 2 * pi * tile_properties['wall_inner_radius']
    wall_length = circumference / (360 / tile_properties['degrees_of_arc'])

    if tile_properties['main_part_blueprint'] == 'OPENLOCK':
        tile_properties['tile_size'][1] = 0.3149

    tile_properties['tile_size'] = Vector((
        wall_length,
        tile_properties['tile_size'][1],
        tile_properties['tile_size'][2]))

    preview_core, displacement_core = create_straight_wall_cores(tile_properties, base)

    cores = [preview_core, displacement_core]
    for core in cores:
        add_deform_modifiers(core, tile_properties['segments'], tile_properties['degrees_of_arc'])

    displacement_core.hide_viewport = True

    return preview_core, displacement_core


def create_openlock_cores(base, tile_properties, tile_empty):
    preview_core, displacement_core = create_wall_cores(base, tile_properties)
    cores = [preview_core, displacement_core]

    cutters = create_openlock_wall_cutters(preview_core, tile_properties)

    for cutter in cutters:
        cutter.parent = base
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True

        for core in cores:
            cutter_bool = core.modifiers.new(cutter.name + '.bool', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = cutter

            # add cutters to object's mt_cutters_collection
            # so we can activate and deactivate them when necessary
            item = core.mt_cutters_collection.add()
            item.name = cutter.name
            item.value = True
            item.parent = core.name

    return preview_core, displacement_core


def create_openlock_wall_cutters(core, tile_properties):
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    core_location = core.location.copy()

    cutters = []

    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    add_object_to_collection(left_cutter_bottom, tile_properties['tile_name'])

    # move cutter to origin and up by 0.63 inches
    left_cutter_bottom.location = Vector((
        core_location[0],
        core_location[1],
        core_location[2] + 0.63))

    circle_center = Vector((
        left_cutter_bottom.location[0],
        left_cutter_bottom.location[1] + tile_properties['wall_inner_radius'],
        left_cutter_bottom.location[2]))

    # rotate cutter
    select(left_cutter_bottom.name)
    activate(left_cutter_bottom.name)
    bpy.ops.transform.rotate(
        value=radians(tile_properties['degrees_of_arc'] / 2),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    # add array
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

    # modify array
    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_properties['tile_size'][2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters
    deselect_all()

    right_cutter_bottom = data_to.objects[0].copy()
    add_object_to_collection(right_cutter_bottom, tile_properties['tile_name'])

    # move cutter to origin and up by 0.63 inches
    right_cutter_bottom.location = Vector((
        core_location[0],
        core_location[1],
        core_location[2] + 0.63))

    # rotate cutter 180 degrees around Z
    right_cutter_bottom.rotation_euler[2] = radians(180)

    circle_center = Vector((
        right_cutter_bottom.location[0],
        right_cutter_bottom.location[1] + tile_properties['wall_inner_radius'],
        right_cutter_bottom.location[2]))

    # rotate cutter around circle center
    select(right_cutter_bottom.name)
    activate(right_cutter_bottom.name)
    bpy.ops.transform.rotate(
        value=-radians(tile_properties['degrees_of_arc'] / 2),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    # add array
    array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_properties['tile_size'][2] - 1

    # make a copy of right_cutter_bottom
    right_cutter_top = right_cutter_bottom.copy()

    add_object_to_collection(right_cutter_top, tile_properties['tile_name'])

    # move cutter up by 0.75 inches
    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

    # modify array
    array_mod = right_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_properties['tile_size'][2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters
