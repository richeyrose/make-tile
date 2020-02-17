""" Contains functions for creating wall tiles """
import os
from math import radians
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.utils import mode
from .. lib.utils.vertex_groups import (
    straight_wall_to_vert_groups,
    construct_displacement_mod_vert_group)
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)
from . create_displacement_mesh import create_displacement_object
from . generic import finalise_tile


def create_straight_wall(tile_props):
    """Creates a straight wall tile
    Keyword arguments:
    tile_empty -- EMPTY, empty which the tile is parented to.
    """
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # then moves base to cursor original location and resets cursor

    scene = bpy.context.scene
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    # A "Tile" is actually a blender collection of loads of meshes. We save properties of our
    # tile in mt_tile_props, a property group on our collection, and a few properties
    # in mt_object_props on each object created by MakeTile
    tile_name = tile_props.tile_name

    # Get base and main part blueprints
    base_blueprint = tile_props.base_blueprint
    main_part_blueprint = tile_props.main_part_blueprint

    tile_meshes = []

    if base_blueprint == 'PLAIN':
        base = create_plain_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'OPENLOCK':
        if main_part_blueprint == 'OPENLOCK':
            tile_props.base_size[0] = tile_props.tile_size[0]
        base = create_openlock_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'NONE':
        # If we have no base create an empty instead for parenting
        tile_props.base_size = (0, 0, 0)
        base = bpy.data.objects.new(tile_name + '.base', None)
        add_object_to_collection(base, tile_name)

    if main_part_blueprint == 'PLAIN':
        preview_core, displacement_core = create_cores(base, tile_props)
        tile_meshes.extend([preview_core, displacement_core])
        displacement_core.hide_viewport = True

    if main_part_blueprint == 'OPENLOCK':
        preview_core, displacement_core = create_openlock_cores(base, tile_props)
        displacement_core.hide_viewport = True
        tile_meshes.extend([preview_core, displacement_core])

    if main_part_blueprint == 'NONE':
        tile_props.tile_size = tile_props.base_size
        preview_core = None

    finalise_tile(base,
                  preview_core,
                  cursor_orig_loc)


#####################################
#              BASE                 #
#####################################


def create_plain_base(tile_props):
    """Returns a base for a wall tile
    """
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    # make base
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    # reposition base and set origin
    '''
    base.location = (
        cursor_orig_loc[0] - base_size[0] / 2,
        cursor_orig_loc[1] - base_size[1] / 2,
        cursor_orig_loc[2])
    '''
    # Where possible we use the native python API rather than operators.
    # If we do use iperators we override the context as this is faster
    # than selecting and deselecting objects and also lets us ignore what
    # object is selected, active etc. Not always possible to do this
    # unfortunately so sometimes we have to use selection

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base]
    }
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name

    return base


def create_openlock_base(tile_props):
    '''Returns an openlock style base with clip sockets'''
    # For OpenLOCK tiles the width and height of the base are constants
    tile_props.base_size = Vector((
        tile_props.base_size[0],
        0.5,
        0.2755))

    # make base
    base = create_plain_base(tile_props)

    # create the slot cutter in the bottom of the base used for stacking tiles
    slot_cutter = create_openlock_base_slot_cutter(base, tile_props, offset=0.236)
    slot_cutter.hide_viewport = False

    # create the clip cutters used for attaching walls to bases
    if base.dimensions[0] >= 1:
        clip_cutter = create_openlock_base_clip_cutter(base, tile_props)
        clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
        clip_boolean.operation = 'DIFFERENCE'
        clip_boolean.object = clip_cutter
        clip_cutter.parent = base
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True

    return base


def create_openlock_base_slot_cutter(base, tile_props, offset=0.236):
    """Makes a cutter for the openlock base slot
    based on the width of the base

    Keyword arguments:
    base -- OBJ, base the cutter will be used on
    """
    # get original location of object and cursor
    base_location = base.location.copy()
    base_size = tile_props.base_size
    
    # work out bool size X from base size, y and z are constants.
    # Correct for negative base dimensions when making curved walls
    if base_size[0] > 0:
        bool_size = [
            base_size[0] - (0.236 * 2),
            0.197,
            0.25]
    else:
        bool_size = [
            base_size[0] + (0.236 * 2),
            0.197,
            0.25]

    cutter = draw_cuboid(bool_size)
    cutter.name = tile_props.tile_name + ".slot_cutter"

    diff = base_size[0] - bool_size[0]
    
    cutter.location = (
        base_location[0] + diff / 2,
        base_location[1] + offset,
        base_location[2] - 0.001)

    ctx = {
        'object': cutter,
        'active_object': cutter,
        'selected_objects': [cutter]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    slot_boolean = base.modifiers.new(cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = cutter
    cutter.parent = base
    cutter.display_type = 'BOUNDS'

    cutter.mt_object_props.is_mt_object = True
    cutter.mt_object_props.geometry_type = 'CUTTER'
    cutter.mt_object_props.tile_name = tile_props.tile_name

    return cutter


def create_openlock_base_clip_cutter(base, tile_props):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- bpy.types.Object, base the cutter will be used on
    """

    mode('OBJECT')

    # get original location of cursor
    base_location = base.location.copy()
    # Get cutter
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load base cutters
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = [
            'openlock.wall.base.cutter.clip',
            'openlock.wall.base.cutter.clip.cap.start',
            'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_props.tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    clip_cutter.location = Vector((
        base_location[0] + 0.5,
        base_location[1] + 0.25,
        base_location[2]))

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_props.base_size[0] - 1

    obj_props = clip_cutter.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    obj_props.geometry_type = 'CUTTER'

    return clip_cutter


#####################################
#              CORE                 #
#####################################
def create_cores(base, tile_props):
    '''Returns the preview and displacement cores'''
    scene = bpy.context.scene

    tile_size = tile_props.tile_size
    tile_name = tile_props.tile_name

    preview_core = create_core(tile_size, base.dimensions, tile_name)
    preview_core.parent = base

    preview_core, displacement_core = create_displacement_object(preview_core)

    preferences = get_prefs()

    primary_material = bpy.data.materials[scene.mt_scene_props.mt_tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

    textured_vertex_groups = ['Front', 'Back']

    # create a vertex group for the displacement modifier
    mod_vert_group_name = construct_displacement_mod_vert_group(displacement_core, textured_vertex_groups)

    assign_displacement_materials(
        displacement_core,
        [image_size, image_size],
        primary_material,
        secondary_material,
        vert_group=mod_vert_group_name)

    assign_preview_materials(
        preview_core,
        primary_material,
        secondary_material,
        textured_vertex_groups)

    preview_core.mt_object_props.geometry_type = 'PREVIEW'
    displacement_core.mt_object_props.geometry_type = 'DISPLACEMENT'

    return preview_core, displacement_core


def create_core(tile_size, base_size, tile_name):
    '''Returns the core (vertical) part of a wall tile
    '''
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    # make our core
    core = draw_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)
    mode('OBJECT')

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0],
        core.location[1] + (base_size[1] - tile_size[1]) / 2,
        cursor_start_loc[2] + base_size[2])

    
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

    diff = base_size[1] - tile_size[1]

    bpy.ops.mesh.bisect(
        plane_co=(tile_size[0] - 0.001, 0, 0),
        plane_no=(1, 0, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(cursor_start_loc[0] + 0.001, 0, 0),
        plane_no=(1, 0, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, tile_size[1] + (diff / 2) - 0.001, 0),
        plane_no=(0, 1, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, cursor_start_loc[1] + (diff / 2) + 0.001, 0),
        plane_no=(0, 1, 0))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, tile_size[2] - 0.01),
        plane_no=(0, 0, 1))
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bisect(
        plane_co=(0, 0, cursor_start_loc[2] + base_size[2] + 0.001),
        plane_no=(0, 0, 1))
    mode('OBJECT')

    bpy.ops.uv.smart_project(ctx, island_margin=0.05)

    straight_wall_to_vert_groups(core)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_name

    return core


def create_openlock_cores(base, tile_props):
    '''Creates the preview and displacement cores and adds side cutters for
    openLOCK clips'''
    # Again width is a constant for OpenLOCK tiles
    tile_props.tile_size = Vector((
        tile_props.tile_size[0],
        0.3149,
        tile_props.tile_size[2]))

    tile_name = tile_props.tile_name

    preview_core, displacement_core = create_cores(base, tile_props)

    wall_cutters = create_openlock_wall_cutters(preview_core, tile_props)
    cores = [preview_core, displacement_core]

    for wall_cutter in wall_cutters:
        wall_cutter.parent = base
        wall_cutter.display_type = 'BOUNDS'
        wall_cutter.hide_viewport = True
        obj_props = wall_cutter.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_name
        obj_props.geometry_type = 'CUTTER'

        for core in cores:
            wall_cutter_bool = core.modifiers.new(wall_cutter.name + '.bool', 'BOOLEAN')
            wall_cutter_bool.operation = 'DIFFERENCE'
            wall_cutter_bool.object = wall_cutter
            wall_cutter_bool.show_render = False

            # add cutters to object's mt_cutters_collection
            # so we can activate and deactivate them when necessary
            item = core.mt_object_props.cutters_collection.add()
            item.name = wall_cutter.name
            item.value = True
            item.parent = core.name

    return preview_core, displacement_core


def create_openlock_wall_cutters(core, tile_props):
    """Creates the cutters for the wall and positions them correctly

    Keyword arguments:
    core -- OBJ, wall core object
    """
    preferences = get_prefs()

    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    core_location = core.location.copy()

    cutters = []
    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_name)
    # get location of bottom front left corner of tile
    front_left = core_location

    # move cutter to bottom front left corner then up by 0.63 inches
    left_cutter_bottom.location = [
        front_left[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of left cutter bottom
    left_cutter_top = left_cutter_bottom.copy()
    left_cutter_top.name = 'X Neg Top.' + tile_name

    add_object_to_collection(left_cutter_top, tile_name)

    # move cutter up by 0.75 inches
    left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters

    right_cutter_bottom = data_to.objects[0].copy()
    right_cutter_bottom.name = 'X Pos Bottom.' + tile_name

    add_object_to_collection(right_cutter_bottom, tile_name)
    # get location of bottom front right corner of tile
    front_right = [
        core_location[0] + (tile_size[0]),
        core_location[1],
        core_location[2]]
    # move cutter to bottom front right corner then up by 0.63 inches
    right_cutter_bottom.location = [
        front_right[0],
        front_right[1] + (base_size[1] / 2),
        front_right[2] + 0.63]
    # rotate cutter 180 degrees around Z
    right_cutter_bottom.rotation_euler[2] = radians(180)

    array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    right_cutter_top = right_cutter_bottom.copy()
    right_cutter_top.name = 'X Pos Top.' + tile_name

    add_object_to_collection(right_cutter_top, tile_name)
    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

    array_mod = right_cutter_top.modifiers["Array"]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters
