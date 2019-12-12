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
    add_displacement_mesh_modifiers,
    add_preview_mesh_modifiers,
    assign_displacement_materials,
    assign_preview_materials)
from .. enums.enums import geometry_types
from . create_straight_wall_tile import (
    create_straight_wall_base,
    create_straight_wall_core,
    create_wall_slabs,
    create_openlock_base_slot_cutter,
    create_openlock_straight_wall_core)


def create_curved_wall(
        tile_blueprint,
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        tile_material,
        base_inner_radius,
        wall_inner_radius,
        degrees_of_arc,
        segments):

    # correct for the Y thickness
    base_inner_radius = base_inner_radius + (base_size[1] / 2)

    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # their then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    if base_system == 'OPENLOCK':
        base_inner_radius = wall_inner_radius + (base_size[1] / 2)
        base_size = Vector((tile_size[0], 0.5, 0.2755))
        base, base_size = create_openlock_curved_wall_base(
            base_size,
            base_inner_radius,
            degrees_of_arc,
            segments,
            tile_name)

    if base_system == 'PLAIN':
        base, base_size = create_plain_curved_wall_base(
            base_size,
            base_inner_radius,
            degrees_of_arc,
            segments,
            tile_name)

    if tile_system == 'OPENLOCK':
        tile_size = Vector((tile_size[0], 0.5, tile_size[2]))
        wall = create_openlock_wall(
            base,
            base_size,
            tile_size,
            wall_inner_radius,
            degrees_of_arc,
            segments,
            tile_name,
            tile_material)

    if tile_system == 'PLAIN':
        wall = create_plain_wall(
            base,
            base_size,
            tile_size,
            wall_inner_radius,
            degrees_of_arc,
            segments,
            tile_name,
            tile_material)
    base.location = cursor_orig_loc
    cursor.location = cursor_orig_loc


def create_openlock_curved_wall_base(
        base_size,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name):

    base, base_size = create_plain_curved_wall_base(
        base_size,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name)

    # make base slot
    slot_cutter = create_openlock_base_slot_cutter(base, base_size, tile_name, offset=0.017)

    cutter_degrees_of_arc = degrees_of_arc * (slot_cutter.dimensions[0] / base_size[0])

    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'
    add_deform_modifiers(slot_cutter, segments, cutter_degrees_of_arc)
    slot_cutter.hide_viewport = True

    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    base_cutter = data_to.objects[0]
    add_object_to_collection(base_cutter, tile_name)

    select(base_cutter.name)
    activate(base_cutter.name)
    bpy.ops.transform.rotate(value=radians(180), orient_axis='Z')
    bpy.ops.object.transform_apply(location=False, scale=False, properties=False)
    loc = base_cutter.location
    circle_center = Vector((loc[0], loc[1] + base_inner_radius, loc[2]))

    # TODO: Introduce check for 360 tile and also small curvature
    bpy.ops.transform.rotate(value=radians((degrees_of_arc / 2) - 22.5), orient_axis='Z', center_override=circle_center)
    bpy.ops.object.transform_apply(location=False, scale=False, properties=False)
    num_cutters = modf((degrees_of_arc - 22.5) / 22.5)
    array_name, empty = add_circle_array(base_cutter, circle_center, num_cutters[1], 'Z', degrees_of_arc - 22.5)
    empty.parent = base
    empty.hide_viewport = True
    base_cutter.parent = base
    base_cutter.display_type = 'BOUNDS'
    base_cutter.hide_viewport = True
    base_cutter_bool = base.modifiers.new('Base Cutter', 'BOOLEAN')
    base_cutter_bool.operation = 'DIFFERENCE'
    base_cutter_bool.object = base_cutter

    return base, base_size


def create_curved_wall_slabs(
        tile_name,
        core_size,
        base_size,
        tile_size,
        segments,
        degrees_of_arc,
        tile_material):

    displacement_type = 'NORMAL'

    slabs = create_wall_slabs(
        displacement_type,
        tile_name,
        core_size,
        base_size,
        tile_size,
        tile_material)

    for slab in slabs:
        slab.hide_viewport = False

        add_deform_modifiers(slab, segments, degrees_of_arc)
        select(slab.name)
        if slab['geometry_type'] == 'DISPLACEMENT':
            slab.hide_viewport = True
    return slabs


def add_deform_modifiers(obj, segments, degrees_of_arc):
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
    curve_mod.angle = radians(degrees_of_arc)
    bpy.ops.object.modifier_move_up(modifier=curve_mod.name)
    bpy.ops.object.modifier_move_up(modifier=curve_mod.name)


def create_openlock_curved_wall_core(tile_name, tile_size, base_size, segments, degrees_of_arc, wall_inner_radius):
    core = create_straight_wall_core(tile_name, tile_size, base_size)
    core_size = core.dimensions.copy()

    add_deform_modifiers(core, segments, degrees_of_arc)

    # add wall cutters
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    side_cutter1 = data_to.objects[0]
    add_object_to_collection(side_cutter1, tile_name)

    core_location = core.location.copy()
    # move cutter to origin and up by 0.63 inches
    side_cutter1.location = Vector((core_location[0], core_location[1], core_location[2] + 0.63))
    circle_center = Vector((side_cutter1.location[0], side_cutter1.location[1] + wall_inner_radius, side_cutter1.location[2]))

    select(side_cutter1.name)
    activate(side_cutter1.name)
    bpy.ops.transform.rotate(value=radians(degrees_of_arc / 2), orient_axis='Z', orient_type='GLOBAL', center_override=circle_center)

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

    side_cutters = [side_cutter1, side_cutter2]
    for cutter in side_cutters:
        cutter.parent = core
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True
        cutter_bool = core.modifiers.new('Wall Cutter', 'BOOLEAN')
        cutter_bool.operation = 'DIFFERENCE'
        cutter_bool.object = cutter

    return core, core_size


def create_curved_wall_core(tile_name, tile_size, base_size, segments, degrees_of_arc):
    core = create_straight_wall_core(tile_name, tile_size, base_size)
    core_size = core.dimensions.copy()

    add_deform_modifiers(core, segments, degrees_of_arc)

    return core, core_size


def create_openlock_wall(
        base,
        base_size,
        tile_size,
        wall_inner_radius,
        degrees_of_arc,
        segments,
        tile_name,
        tile_material):
    # correct for the Y thickness
    wall_inner_radius = wall_inner_radius + (tile_size[1] / 2)

    circumference = 2 * pi * wall_inner_radius
    wall_length = circumference / (360 / degrees_of_arc)
    tile_size = Vector((wall_length, tile_size[1] - 0.1850, tile_size[2]))

    core, core_size = create_openlock_curved_wall_core(
        tile_name,
        tile_size,
        base_size,
        segments,
        degrees_of_arc,
        wall_inner_radius)

    core.parent = base

    slabs = create_curved_wall_slabs(
        tile_name,
        core_size,
        base_size,
        tile_size,
        segments,
        degrees_of_arc,
        tile_material)

    for slab in slabs:
        slab.parent = base


def create_plain_wall(
        base,
        base_size,
        tile_size,
        wall_inner_radius,
        degrees_of_arc,
        segments,
        tile_name,
        tile_material):

    # correct for the Y thickness
    wall_inner_radius = wall_inner_radius + (tile_size[1] / 2)

    circumference = 2 * pi * wall_inner_radius
    wall_length = circumference / (360 / degrees_of_arc)
    tile_size = Vector((wall_length, tile_size[1] - 0.1850, tile_size[2]))

    core, core_size = create_curved_wall_core(tile_name, tile_size, base_size, segments, degrees_of_arc)
    core.parent = base
    slabs = create_curved_wall_slabs(tile_name, core_size, base_size, tile_size, segments, degrees_of_arc, tile_material)

    for slab in slabs:
        slab.parent = base


def create_plain_curved_wall_base(
        base_size,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name):

    circumference = 2 * pi * base_inner_radius

    base_length = circumference / (360 / degrees_of_arc)
    base_size = Vector((base_length, base_size[1], base_size[2]))

    base = create_straight_wall_base(tile_name, base_size)
    add_deform_modifiers(base, segments, degrees_of_arc)

    return base, base_size
