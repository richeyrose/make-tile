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
from .. lib.utils.utils import mode, view3d_find, add_circle_array
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    assign_displacement_materials_2,
    assign_preview_materials_2)
from .. enums.enums import geometry_types
from . create_straight_wall_tile import (
    create_straight_wall_base,
    create_straight_wall_core_2,
    create_openlock_base_slot_cutter,
    create_openlock_straight_wall_core_2)


def create_curved_wall(tile_empty):
    """Returns a curved wall"""

    tile_properties = tile_empty['tile_properties']

    # correct for the Y thickness
    tile_properties['base_inner_radius'] = tile_properties['base_inner_radius'] + (tile_properties['base_size'][1] / 2)

    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_inner_radius'] = tile_properties['wall_inner_radius'] + (tile_properties['base_size'][1] / 2)
        tile_properties['base_size'] = Vector((tile_properties['tile_size'][0], 0.5, 0.2755))
        base, tile_properties['base_size'] = create_openlock_curved_wall_base(tile_properties)

    if tile_properties['base_blueprint'] == 'PLAIN':
        base, tile_properties['base_size'] = create_plain_curved_wall_base(tile_properties)

    if tile_properties['tile_blueprint'] == 'OPENLOCK':
        tile_properties['tile_size'] = Vector((tile_properties['tile_size'][0], 0.5, tile_properties['tile_size'][2]))
        wall = create_openlock_wall_2(base, tile_properties, tile_empty)

    if tile_properties['tile_blueprint'] == 'PLAIN':
        wall = create_plain_wall_2(base, tile_properties, tile_empty)

    tile_empty['tile_properties'] = tile_properties

    wall[1].hide_viewport = True
    base.location = cursor_orig_loc
    cursor.location = cursor_orig_loc


def create_openlock_curved_wall_base(tile_properties):

    base, tile_properties['base_size'] = create_plain_curved_wall_base(tile_properties)

    # make base slot
    if tile_properties['base_socket_sides'] == 'INNER':
        slot_cutter = create_openlock_base_slot_cutter(base, tile_properties, offset=0.017)
    else:
        slot_cutter = create_openlock_base_slot_cutter(base, tile_properties['base_size'], tile_properties['tile_name'])
    cutter_degrees_of_arc = tile_properties['degrees_of_arc'] * (slot_cutter.dimensions[0] / tile_properties['base_size'][0])

    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'
    add_deform_modifiers(slot_cutter, tile_properties['segments'], tile_properties)
    slot_cutter.hide_viewport = True

    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load base cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    base_cutter = data_to.objects[0]
    add_object_to_collection(base_cutter, tile_properties['tile_name'])

    select(base_cutter.name)
    activate(base_cutter.name)

    if tile_properties['base_socket_sides'] == 'INNER':
        bpy.ops.transform.rotate(value=radians(180), orient_axis='Z')
        bpy.ops.object.transform_apply(location=False, scale=False, properties=False)

    loc = base_cutter.location
    circle_center = Vector((loc[0], loc[1] + tile_properties['base_inner_radius'], loc[2]))

    bpy.ops.transform.rotate(value=radians((tile_properties['degrees_of_arc'] / 2) - 22.5), orient_axis='Z', center_override=circle_center)
    bpy.ops.object.transform_apply(location=False, scale=False, properties=False)
    num_cutters = modf((tile_properties['degrees_of_arc'] - 22.5) / 22.5)
    array_name, empty = add_circle_array(base_cutter, circle_center, num_cutters[1], 'Z', tile_properties['degrees_of_arc'] - 22.5)
    empty.parent = base
    empty.hide_viewport = True
    base_cutter.parent = base
    base_cutter.display_type = 'BOUNDS'
    base_cutter.hide_viewport = True
    base_cutter_bool = base.modifiers.new('Base Cutter', 'BOOLEAN')
    base_cutter_bool.operation = 'DIFFERENCE'
    base_cutter_bool.object = base_cutter

    return base, tile_properties['base_size']


def add_deform_modifiers(obj, segments, tile_properties):
    deselect_all()
    select(obj.name)
    activate(obj.name)

    # loopcut
    mode('EDIT')
    region, rv3d, v3d, area = view3d_find(True)

    override = {
        'scene': bpy.context.scene,
        'region': region,
        'area': area,
        'space': v3d
    }

    bpy.ops.mesh.loopcut(override, number_cuts=segments - 2, smoothness=0, falloff='INVERSE_SQUARE', object_index=0, edge_index=2)

    mode('OBJECT')

    curve_mod = obj.modifiers.new("curve", "SIMPLE_DEFORM")
    curve_mod.deform_method = 'BEND'
    curve_mod.deform_axis = 'Z'
    curve_mod.show_render = False
    curve_mod.angle = radians(tile_properties['degrees_of_arc'])

    return curve_mod.name


def create_openlock_wall_2(base, tile_properties, tile_empty):

    wall = create_plain_wall_2(base, tile_properties, tile_empty)

    cutters = create_openlock_wall_cutters(wall[0], tile_properties)

    for cutter in cutters:
        cutter.parent = base
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True

        for core in wall:
            cutter_bool = core.modifiers.new('Wall Cutter', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = cutter
    return wall


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
    if tile_properties['textured_faces']['x_neg'] is 0:
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

    if tile_properties['textured_faces']['x_pos'] is 0:
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


def create_plain_wall_2(base, tile_properties, tile_empty):

    # correct for the Y thickness
    tile_properties['wall_inner_radius'] = tile_properties['wall_inner_radius'] + (tile_properties['tile_size'][1] / 2)

    circumference = 2 * pi * tile_properties['wall_inner_radius']
    wall_length = circumference / (360 / tile_properties['degrees_of_arc'])
    tile_properties['tile_size'] = Vector((wall_length, 0.3149, tile_properties['tile_size'][2]))

    preview_core = create_straight_wall_core_2(tile_properties)
    preview_core['geometry_type'] = 'PREVIEW'

    displacement_core = create_straight_wall_core_2(tile_properties)
    displacement_core['geometry_type'] = 'DISPLACEMENT'

    preview_core['displacement_obj'] = displacement_core
    displacement_core['preview_obj'] = preview_core

    cores = [preview_core, displacement_core]

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_properties['tile_materials']['tile_material_1']]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials_2(displacement_core, [image_size, image_size], primary_material, secondary_material, tile_properties['textured_faces'])
    assign_preview_materials_2(preview_core, primary_material, secondary_material, tile_properties['textured_faces'])

    for core in cores:
        core.parent = base
        add_deform_modifiers(core, tile_properties['segments'], tile_properties)
    tile_empty['tile_properties'] = tile_properties

    return cores


def create_plain_curved_wall_base(tile_properties):

    circumference = 2 * pi * tile_properties['base_inner_radius']

    base_length = circumference / (360 / tile_properties['degrees_of_arc'])
    tile_properties['base_size'] = Vector((base_length, tile_properties['base_size'][1], tile_properties['base_size'][2]))

    base = create_straight_wall_base(tile_properties)
    add_deform_modifiers(base, tile_properties['segments'], tile_properties)

    return base, tile_properties['base_size']