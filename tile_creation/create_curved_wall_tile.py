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

from .. lib.utils.utils import (
    mode,
    view3d_find,
    add_circle_array,
    add_deform_modifiers)

from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups

from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    assign_displacement_materials,
    assign_preview_materials)

from .. enums.enums import geometry_types

from . create_straight_wall_tile import (
    create_plain_base as create_plain_straight_wall_base,
    create_cores as create_straight_wall_cores,
    create_core,
    create_openlock_base_slot_cutter)

from .. operators.trim_tile import (
    create_curved_wall_tile_trimmers,
    add_bool_modifier)


# TODO: Make it work for "negative" degrees of arc for openlock
def create_curved_wall(tile_empty):
    """Creates a curved wall tile"""
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    scene = bpy.context.scene
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    tile_props = bpy.context.collection.mt_tile_props
    tile_name = tile_props.tile_name

    # Get base and main part blueprints
    base_blueprint = tile_props.base_blueprint
    main_part_blueprint = tile_props.main_part_blueprint

    # Get tile dimensions
    tile_props.base_radius = scene.mt_base_radius
    tile_props.wall_radius = scene.mt_wall_radius
    tile_props.segments = scene.mt_segments

    # We store a list of meshes here because we're going to add
    # trimmer modifiers to all of them later but we don't yet
    # know the full dimensions of our tile
    tile_meshes = []

    if base_blueprint == 'OPENLOCK':
        # TODO: Check this. Shouldn't it be a constant?
        tile_props.base_radius = tile_props.wall_radius + scene.mt_base_y / 2
        tile_props.base_size = Vector((
            scene.mt_tile_x,
            0.5,
            0.2755))
        base = create_openlock_base(tile_props.base_radius, tile_props.base_size, tile_name)
        tile_meshes.append(base)

    if base_blueprint == 'PLAIN':
        tile_props.base_radius = tile_props.base_radius + scene.mt_base_y / 2
        tile_props.base_size = Vector((
            scene.mt_base_x,
            scene.mt_base_y,
            scene.mt_base_z
        ))
        base = create_plain_base(tile_props.base_radius, tile_props.base_size, tile_name)
        tile_meshes.append(base)

    if main_part_blueprint == 'OPENLOCK':
        tile_props.tile_size = Vector((
            scene.mt_tile_x,
            0.5,
            scene.mt_tile_z))
        preview_core, displacement_core = create_openlock_cores(base)
        tile_meshes.extend([preview_core, displacement_core])

    if main_part_blueprint == 'PLAIN':
        tile_props.tile_size = Vector((
            scene.mt_tile_x,
            scene.mt_tile_y,
            scene.mt_tile_z))
        preview_core, displacement_core = create_wall_cores(base)
        displacement_core.hide_viewport = True
        tile_meshes.extend([preview_core, displacement_core])

    # create tile trimmers. Used to ensure that displaced
    # textures don't extend beyond the original bounds of the tile.
    trimmers = create_curved_wall_tile_trimmers(
        tile_props.tile_size,
        tile_props.base_size,
        tile_name,
        base_blueprint,
        tile_empty)

    for obj in tile_meshes:
        for trimmer in trimmers:
            add_bool_modifier(obj, trimmer.name)
            trimmer.display_type = 'WIRE'
            trimmer.hide_viewport = True
    base.parent = tile_empty

    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc


def create_plain_base(base_radius, base_size, tile_name):
    scene = bpy.context.scene
    tile_props = bpy.context.collection.mt_tile_props

    tile_props.degrees_of_arc = scene.mt_degrees_of_arc
    circumference = 2 * pi * base_radius
    base_length = circumference / (360 / tile_props.degrees_of_arc)
    tile_props.base_size[0] = base_length

    base = create_plain_straight_wall_base(tile_name, base_size)
    add_deform_modifiers(base,
                         scene.mt_segments,
                         tile_props.degrees_of_arc)

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name

    return base


def create_openlock_base(base_radius, base_size, tile_name):
    scene = bpy.context.scene
    base = create_plain_base(base_radius, base_size, tile_name)
    slot_cutter = create_openlock_base_slot_cutter(base)
    # Bit of a guestimate this
    if base_size[0] > 0:
        cutter_arc = scene.mt_degrees_of_arc - 12.5
    else:
        cutter_arc = scene.mt_degrees_of_arc + 12.5

    add_deform_modifiers(
        slot_cutter,
        scene.mt_segments,
        cutter_arc)

    slot_cutter.hide_viewport = True

    clip_cutter = create_openlock_base_clip_cutter(base)

    return base


def create_openlock_base_clip_cutter(base):
    # load base cutter
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")
    tile_props = bpy.context.collection.mt_tile_props

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    clip_cutter = data_to.objects[0]
    add_object_to_collection(clip_cutter, tile_props.tile_name)

    deselect_all()
    select(clip_cutter.name)

    # TODO: Override context. Haven't worked out what we need for it yet
    bpy.ops.transform.rotate(value=radians(180), orient_axis='Z')
    bpy.ops.object.transform_apply(location=False, scale=False, properties=False)

    loc = clip_cutter.location

    if tile_props.degrees_of_arc > 0:
        y_offset = loc[1] + tile_props.base_radius
    else:
        y_offset = loc[1] - tile_props.base_radius

    circle_center = Vector((
        loc[0],
        y_offset,
        loc[2]))

    if tile_props.degrees_of_arc > 0:
        rot_offset = (tile_props.degrees_of_arc / 2) - 22.5
    else:
        rot_offset = (tile_props.degrees_of_arc / 2) + 22.5

    bpy.ops.transform.rotate(
        value=radians(rot_offset),
        orient_axis='Z',
        center_override=circle_center)

    bpy.ops.object.transform_apply(
        location=False,
        scale=False,
        properties=False)

    if tile_props.degrees_of_arc > 0:
        num_cutters = modf((tile_props.degrees_of_arc - 22.5) / 22.5)
    else:
        num_cutters = modf((tile_props.degrees_of_arc * -1 - 22.5) / 22.5)

    if tile_props.degrees_of_arc > 0:
        rot_offset = tile_props.degrees_of_arc - 22.5
    else:
        rot_offset = tile_props.degrees_of_arc + 22.5

    array_name, empty = add_circle_array(
        clip_cutter,
        circle_center,
        num_cutters[1],
        'Z',
        rot_offset)

    empty.parent = base
    empty.hide_viewport = True

    clip_cutter.parent = base
    clip_cutter.display_type = 'WIRE'
    clip_cutter.hide_viewport = True
    clip_cutter_bool = base.modifiers.new('Base Cutter', 'BOOLEAN')
    clip_cutter_bool.operation = 'DIFFERENCE'
    clip_cutter_bool.object = clip_cutter

    obj_props = clip_cutter.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    obj_props.geometry_type = 'CUTTER'

    return clip_cutter


def create_wall_cores(base):
    tile_props = bpy.context.collection.mt_tile_props
    # calculate wall dimensions

    tile_props.wall_radius = (
        tile_props.wall_radius + tile_props.tile_size[1] / 2)

    circumference = 2 * pi * tile_props.wall_radius
    wall_length = circumference / (360 / tile_props.degrees_of_arc)

    if tile_props.main_part_blueprint == 'OPENLOCK':
        tile_props.tile_size[1] = 0.3149

    tile_props.tile_size = Vector((
        wall_length,
        tile_props.tile_size[1],
        tile_props.tile_size[2]))

    preview_core, displacement_core = create_straight_wall_cores(
        base,
        tile_props.tile_size,
        tile_props.tile_name)

    cores = [preview_core, displacement_core]

    for core in cores:
        add_deform_modifiers(
            core,
            segments=tile_props.segments,
            degrees_of_arc=tile_props.degrees_of_arc)

    displacement_core.hide_viewport = True

    return preview_core, displacement_core


def create_openlock_cores(base):

    tile_props = bpy.context.collection.mt_tile_props

    preview_core, displacement_core = create_wall_cores(base)
    cores = [preview_core, displacement_core]

    cutters = create_openlock_wall_cutters(preview_core)

    for cutter in cutters:
        obj_props = cutter.mt_object_props
        cutter.parent = base
        cutter.display_type = 'WIRE'
        cutter.hide_viewport = True
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        obj_props.geometrt_type = 'CUTTER'

        for core in cores:
            cutter_bool = core.modifiers.new(cutter.name + '.bool', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = cutter

            # add cutters to object's mt_cutters_collection
            # so we can activate and deactivate them when necessary
            item = core.mt_object_props.cutters_collection.add()
            item.name = cutter.name
            item.value = True
            item.parent = core.name

    return preview_core, displacement_core


def create_openlock_wall_cutters(core):
    deselect_all()

    tile_props = bpy.context.collection.mt_tile_props
    tile_name = tile_props.tile_name

    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    core_location = core.location.copy()

    cutters = []

    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_props.tile_name)

    # move cutter to origin and up by 0.63 inches
    left_cutter_bottom.location = Vector((
        core_location[0],
        core_location[1],
        core_location[2] + 0.63))

    if tile_props.degrees_of_arc > 0:
        circle_center = Vector((
            left_cutter_bottom.location[0],
            left_cutter_bottom.location[1] + tile_props.wall_radius,
            left_cutter_bottom.location[2]))
    else:
        circle_center = Vector((
            left_cutter_bottom.location[0],
            left_cutter_bottom.location[1] - tile_props.wall_radius,
            left_cutter_bottom.location[2]))

    # rotate cutter
    select(left_cutter_bottom.name)
    activate(left_cutter_bottom.name)
    bpy.ops.transform.rotate(
        value=radians(tile_props.degrees_of_arc / 2),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    # add array
    array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_props.tile_size[2] - 1

    # make a copy of left cutter bottom
    left_cutter_top = left_cutter_bottom.copy()
    left_cutter_top.name = 'X Neg Top.' + tile_name

    add_object_to_collection(left_cutter_top, tile_props.tile_name)

    # move cutter up by 0.75 inches
    left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

    # modify array
    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_props.tile_size[2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters
    deselect_all()

    right_cutter_bottom = data_to.objects[0].copy()
    right_cutter_bottom.name = 'X Pos Bottom.' + tile_name

    add_object_to_collection(right_cutter_bottom, tile_props.tile_name)

    # move cutter to origin and up by 0.63 inches
    right_cutter_bottom.location = Vector((
        core_location[0],
        core_location[1],
        core_location[2] + 0.63))

    # rotate cutter 180 degrees around Z
    right_cutter_bottom.rotation_euler[2] = radians(180)

    if tile_props.degrees_of_arc > 0:
        circle_center = Vector((
            right_cutter_bottom.location[0],
            right_cutter_bottom.location[1] + tile_props.wall_radius,
            right_cutter_bottom.location[2]))
    else:
        circle_center = Vector((
            right_cutter_bottom.location[0],
            right_cutter_bottom.location[1] - tile_props.wall_radius,
            right_cutter_bottom.location[2]))

    # rotate cutter around circle center
    select(right_cutter_bottom.name)
    activate(right_cutter_bottom.name)
    bpy.ops.transform.rotate(
        value=-radians(tile_props.degrees_of_arc / 2),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    # add array
    array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_props.tile_size[2] - 1

    # make a copy of right_cutter_bottom
    right_cutter_top = right_cutter_bottom.copy()
    right_cutter_top.name = 'X Pos Top.' + tile_name

    add_object_to_collection(right_cutter_top, tile_props.tile_name)

    # move cutter up by 0.75 inches
    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

    # modify array
    array_mod = right_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_props.tile_size[2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters
