import os
import math
import bpy

from bpy.types import Operator, Panel
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

from ..lib.bmturtle.scripts import draw_cuboid, draw_rectangular_floor_core
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.utils.utils import mode, get_all_subclasses
from .. utils.registration import get_prefs

from .create_tile import (
    convert_to_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props)


class MT_PT_Rect_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Rect_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "RECT_FLOOR"
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

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')
        row.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Openlock_Rect_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK rectangular base."""

    bl_idname = "object.make_openlock_rect_base"
    bl_label = "Rectangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "RECT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Rect_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain rectangular base."""

    bl_idname = "object.make_plain_rect_base"
    bl_label = "Rectangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "RECT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Rect_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty rectangular base."""

    bl_idname = "object.make_empty_rect_base"
    bl_label = "Rectangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "RECT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Rect_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain rectangular core."""

    bl_idname = "object.make_plain_rect_floor_core"
    bl_label = "Rectangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "RECT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        create_plain_rect_floor_cores(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Rect_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock rectangular floor core."""

    bl_idname = "object.make_openlock_rect_floor_core"
    bl_label = "Rectangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "RECT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        bpy.ops.object.make_plain_rect_floor_core()
        return{'FINISHED'}


class MT_OT_Make_Empty_Rect_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty rectangular floor core."""

    bl_idname = "object.make_empty_rect_floor_core"
    bl_label = "Rectangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "RECT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Rect_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a rectangular floor tile with a customisable base and main part."""

    bl_idname = "object.make_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "RECT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'RECT_BASE'
        core_type = 'RECT_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(
            context, scene_props)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            core = None
        else:
            core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer

        return {'FINISHED'}


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
    original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'RECT_FLOOR'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def create_plain_rect_floor_cores(tile_props):
    """Create preview and displacement cores.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_floor_core(tile_props)
    textured_vertex_groups = ['Top']

    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)

    bpy.context.view_layer.objects.active = preview_core

    return preview_core


def spawn_floor_core(tile_props):
    """Spawn the core (top part) of a floor tile.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile core
    """
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name
    native_subdivisions = (
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions
    )

    core = draw_rectangular_floor_core(
        [tile_size[0],
         tile_size[1],
         tile_size[2] - base_size[2]],
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    core.location[2] = core.location[2] + base_size[2]

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core


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
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base]}

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

    base = spawn_plain_base(tile_props)

    slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props)
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    clip_cutters = spawn_openlock_base_clip_cutters(base, tile_props)

    for clip_cutter in clip_cutters:
        set_bool_obj_props(clip_cutter, base, tile_props)
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    mode('OBJECT')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(base, tile_props):
    """Spawn an openlock base slot cutter into scene and positions it correctly.

    Args:
        base (bpy.types.Object): base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.type.Object: slot cutter
    """
    mode('OBJECT')

    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "rect_floor_slot_cutter.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = [
            'corner_xneg_yneg',
            'corner_xneg_ypos',
            'corner_xpos_yneg',
            'corner_xpos_ypos',
            'slot_cutter_a',
            'slot_cutter_b',
            'slot_cutter_c',
            'base_slot_cutter_final']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_props.tile_name)

    for obj in data_to.objects:
        obj.hide_viewport = True

    cutter_a = data_to.objects[4]
    cutter_b = data_to.objects[5]
    cutter_c = data_to.objects[6]
    cutter_d = data_to.objects[7]

    cutter_d.name = 'Base Slot Cutter.' + tile_props.tile_name

    a_array = cutter_a.modifiers['Array']
    a_array.fit_length = base.dimensions[1] - 1.014

    b_array = cutter_b.modifiers['Array']
    b_array.fit_length = base.dimensions[0] - 1.014

    c_array = cutter_c.modifiers['Array']
    c_array.fit_length = base.dimensions[0] - 1.014

    d_array = cutter_d.modifiers['Array']
    d_array.fit_length = base.dimensions[1] - 1.014

    cutter_d.location = (
        base_location[0] + 0.24,
        base_location[1] + 0.24,
        base_location[2] + 0.24)

    return cutter_d


def spawn_openlock_base_clip_cutters(base, tile_props):
    """Make cutters for the openlock base clips.

    Args:
        base (bpy.types.Object): tile base
        tile_props (mt_tile_props): tile properties

    Returns:
        list[bpy.types.Object]

    """
    mode('OBJECT')

    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = [
            'openlock.wall.base.cutter.clip',
            'openlock.wall.base.cutter.clip.cap.start',
            'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_props.tile_name)

    clip_cutter = data_to.objects[0]
    clip_cutter.name = 'Y Neg Clip.' + base.name
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    # get location of bottom front left corner of tile
    front_left = (
        base_location[0],
        base_location[1],
        base_location[2])

    clip_cutter.location = (
        front_left[0] + 0.5,
        front_left[1] + 0.25,
        front_left[2])

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base.dimensions[0] - 1

    clip_cutter2 = clip_cutter.copy()
    clip_cutter2.name = 'X Pos Clip.' + base.name
    clip_cutter2.data = clip_cutter2.data.copy()

    add_object_to_collection(clip_cutter2, tile_props.tile_name)
    clip_cutter2.rotation_euler = (0, 0, math.radians(90))

    front_right = (
        base_location[0] + base.dimensions[0],
        base_location[1],
        base_location[2])

    clip_cutter2.location = (
        front_right[0] - 0.25,
        front_right[1] + 0.5,
        front_right[2])

    array_mod2 = clip_cutter2.modifiers['Array']
    array_mod2.fit_type = 'FIT_LENGTH'
    array_mod2.fit_length = base.dimensions[1] - 1

    clip_cutter3 = clip_cutter.copy()
    clip_cutter3.name = 'Y Pos Clip.' + base.name
    clip_cutter3.data = clip_cutter3.data.copy()
    add_object_to_collection(clip_cutter3, tile_props.tile_name)

    clip_cutter3.rotation_euler = (0, 0, math.radians(180))

    clip_cutter3.location = (
        clip_cutter.location[0] + base.dimensions[0] - 1,
        clip_cutter.location[1] + base.dimensions[1] - 0.5,
        clip_cutter.location[2]
    )
    array_mod3 = clip_cutter3.modifiers['Array']
    array_mod3.fit_type = 'FIT_LENGTH'
    array_mod3.fit_length = base.dimensions[0] - 1

    clip_cutter4 = clip_cutter2.copy()
    clip_cutter4.name = 'X Neg Clip.' + base.name
    clip_cutter4.data = clip_cutter4.data.copy()
    add_object_to_collection(clip_cutter4, tile_props.tile_name)

    clip_cutter4.rotation_euler = (0, 0, math.radians(-90))

    clip_cutter4.location = (
        clip_cutter2.location[0] - base.dimensions[0] + 0.5,
        clip_cutter2.location[1] + base.dimensions[1] - 1,
        clip_cutter2.location[2]
    )

    array_mod4 = clip_cutter4.modifiers['Array']
    array_mod4.fit_type = 'FIT_LENGTH'
    array_mod4.fit_length = base.dimensions[1] - 1

    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

    return [clip_cutter, clip_cutter2, clip_cutter3, clip_cutter4]
