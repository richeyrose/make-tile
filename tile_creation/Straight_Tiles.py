import os
from math import radians, floor
from mathutils import Vector
import bpy

from bpy.types import Operator, Panel
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from ..lib.bmturtle.scripts import (
    draw_cuboid,
    draw_straight_wall_core)
from .. lib.utils.utils import mode, get_all_subclasses

from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props,
    get_subdivs)

from .Rectangular_Tiles import create_plain_rect_floor_cores as create_plain_floor_cores


class MT_PT_Straight_Wall_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Straight_Wall_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "STRAIGHT_WALL"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        wall_props = scene.mt_wall_scene_props

        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_z')

        layout.label(text="Core Size")
        layout.prop(scene_props, 'tile_y', text="Width")

        if scene_props.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.label(text="Floor Thickness")
            layout.prop(wall_props, 'floor_thickness', text="")
            layout.label(text="Wall Position"),
            layout.prop(wall_props, 'wall_position', text="")


        layout.label(text="Lock Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')
        row.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.operator('scene.reset_wall_defaults')


class MT_PT_Straight_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Straight_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "STRAIGHT_FLOOR"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_y')
        row.prop(scene_props, 'tile_z')

        layout.label(text="Lock Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')
        row.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Openlock_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK straight base."""

    bl_idname = "object.make_openlock_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_S_Wall_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK straight base."""

    bl_idname = "object.make_openlock_s_wall_straight_base"
    bl_label = "S Wall Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK_S_WALL"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight base."""

    bl_idname = "object.make_plain_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight base."""

    bl_idname = "object.make_empty_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight wall core."""

    bl_idname = "object.make_plain_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        spawn_plain_wall_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Wall_Core(MT_OT_Make_Plain_Straight_Wall_Core, Operator):
    """Internal Operator. Generate an openlock straight wall core."""

    bl_idname = "object.make_openlock_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        base = context.active_object
        spawn_openlock_wall_cores(self, tile_props, base)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight wall core."""

    bl_idname = "object.make_empty_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Plain_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight floor core."""

    bl_idname = "object.make_plain_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        create_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock straight floor core."""

    bl_idname = "object.make_openlock_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        create_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight wall core."""

    bl_idname = "object.make_empty_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Straight_Wall_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_WALL"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        wall_scene_props = scene.mt_wall_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_WALL_CORE'

        cursor_orig_loc, cursor_orig_rot = initialise_wall_creator(context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)
        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)
        tile_props = context.collection.mt_tile_props
        orig_tile_size = []
        for c, v in enumerate(tile_props.tile_size):
            orig_tile_size.append(v)

        tile_props.tile_size = (
            tile_props.base_size[0],
            tile_props.base_size[1],
            scene_props.base_z + wall_scene_props.floor_thickness)
        if base_blueprint in {'OPENLOCK_S_WALL', 'PLAIN_S_WALL'}:
            floor_core = spawn_prefab(context, subclasses, 'OPENLOCK', 'STRAIGHT_FLOOR_CORE')
        tile_props.tile_size = orig_tile_size

        finalise_tile(base, (preview_core, floor_core), cursor_orig_loc, cursor_orig_rot)

        # scene.render.engine = original_renderer

        return {'FINISHED'}


class MT_OT_Make_Straight_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_floor"
    bl_label = "Straight Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # scene.render.engine = original_renderer

        return {'FINISHED'}


def initialise_wall_creator(context, scene_props):
    """Initialise the wall creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (MakeTile.properties.MT_Scene_Properties): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Walls', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Walls'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'STRAIGHT_WALL'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    return cursor_orig_loc, cursor_orig_rot


def initialise_floor_creator(context, scene_props):
    """Initialise the floor creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (MakeTile.properties.MT_Scene_Properties): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'STRAIGHT_FLOOR'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    return cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    # make base
    # base = draw_cuboid(base_size)
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

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
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn an openlock base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """

    # make base
    base = spawn_plain_base(tile_props)

    # create the slot cutter in the bottom of the base used for stacking tiles
    slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props, offset=0.236)
    set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    # create the clip cutters used for attaching walls to bases
    if base.dimensions[0] >= 1:
        clip_cutter = spawn_openlock_base_clip_cutter(base, tile_props)
        set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(base, tile_props, offset=0.236):
    """Makes a cutter for the openlock base slot
    based on the width of the base
    """
    # get original location of object and cursor
    base_location = base.location.copy()
    base_size = tile_props.base_size

    # work out bool size X from base size, y and z are constants.
    bool_size = [
        base_size[0] - (offset * 2),
        0.197,
        0.25]

    cutter = draw_cuboid(bool_size)
    cutter.name = 'Base Slot.' + tile_props.tile_name + ".slot_cutter"

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

    base.select_set(False)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    return cutter


def spawn_openlock_base_clip_cutter(base, tile_props):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly
    """

    mode('OBJECT')

    # get original location of cursor
    base_location = base.location.copy()

    # Get cutter
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

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

    # cutter_start_cap.hide_set(True)
    # cutter_end_cap.hide_set(True)
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

    clip_cutter.name = 'Clip Cutter.' + base.name

    return clip_cutter


def spawn_plain_wall_cores(self, tile_props):
    """Spawn plain Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    preview_core = spawn_wall_core(self, tile_props)
    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)
    return preview_core


def spawn_openlock_wall_cores(self, tile_props, base):
    """Spawn OpenLOCK core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        base (bpy.types.Object): tile base

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_wall_core(self, tile_props)

    wall_cutters = spawn_openlock_wall_cutters(
        core,
        tile_props)

    if tile_props.tile_size[0] > 1:
        top_pegs = spawn_openlock_top_pegs(
            core,
            tile_props)

        set_bool_obj_props(top_pegs, base, tile_props, 'UNION')
        set_bool_props(top_pegs, core, 'UNION')

    for wall_cutter in wall_cutters:
        set_bool_obj_props(wall_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(wall_cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        core,
        textured_vertex_groups)

    return core


def spawn_wall_core(self, tile_props):
    """Return the core (vertical) part of a straight wall tile."""
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    core_size = [
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]]
    tile_name = tile_props.tile_name
    native_subdivisions = get_subdivs(tile_props.subdivision_density, core_size)

    core = draw_straight_wall_core(
        core_size,
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0],
        core.location[1] + (base_size[1] - tile_size[1]) / 2,
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_openlock_top_pegs(core, tile_props):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        core (bpy.types.Object): tile core
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    peg = load_openlock_top_peg(tile_props)

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 0.505
    array_mod.fit_type = 'FIXED_COUNT'
    array_mod.count = 2

    core_location = core.location.copy()

    if tile_size[0] < 4 and tile_size[0] >= 1:
        peg.location = (
            core_location[0] + (tile_size[0] / 2) - 0.252,
            core_location[1] + (base_size[1] / 2) + 0.08,
            core_location[2] + tile_size[2])
    else:
        peg.location = (
            core_location[0] + 0.756,
            core_location[1] + (base_size[1] / 2) + 0.08,
            core_location[2] + tile_size[2])
        array_mod = peg.modifiers.new('Array', 'ARRAY')
        array_mod.use_relative_offset = False
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace[0] = 2.017
        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_size[0] - 1.3

    return peg


def spawn_openlock_wall_cutters(core, tile_props):
    """Creates the cutters for the wall and positions them correctly
    """
    preferences = get_prefs()

    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

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
    array_mod.constant_offset_displace = [0, 0, 2]
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
    array_mod.constant_offset_displace = [0, 0, 2]
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
