import bpy

from bpy.types import Operator, Panel
from .. utils.registration import get_prefs
from .. lib.utils.utils import mode, get_all_subclasses
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)
from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg)
from ..lib.bmturtle.scripts import (
    draw_cuboid,
    draw_straight_wall_core)
from .Rectangular_Tiles import spawn_openlock_base

class MT_PT_Connecting_Column_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Connecting_Column_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "CONNECTING_COLUMN"
        return False

    def draw(self, context):
        """Draw the Panel.

        Args:
            context (bpy.context): context
        """
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.prop(scene_props, 'column_type')

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'tile_blueprint')

        layout.label(text="Column Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_y')
        row.prop(scene_props, 'tile_z')

        layout.label(text="Lock Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Openlock_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK connecting column base."""

    bl_idname = "object.make_openlock_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain connecting column base."""

    bl_idname = "object.make_plain_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty connecting column base."""

    bl_idname = "object.make_empty_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain connecting column core."""

    bl_idname = "object.make_plain_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_connecting_column_core(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock connecting column core."""

    bl_idname = "object.make_openlock_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_openlock_connecting_column_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty connecting column core."""

    bl_idname = "object.make_empty_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Connecting_Column_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a connecting column tile with a customisable base and main part."""

    bl_idname = "object.make_connecting_column"
    bl_label = "Connecting Column"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "CONNECTING_COLUMN"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'CONNECTING_COLUMN_BASE'
        core_type = 'CONNECTING_COLUMN_CORE'

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_column_creator(context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer

        return {'FINISHED'}


def initialise_column_creator(context, scene_props):
    """Initialise the column creator and set common properties.

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
    create_collection('Columns', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Columns'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'CONNECTING_COLUMN'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot



def spawn_openlock_connecting_column_cores(base, tile_props):
    """Spawn OpenLOCK Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    preview_core = spawn_connecting_column_core(tile_props)
    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)
    return preview_core


def spawn_plain_connecting_column_core(tile_props):
    """Spawn plain Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    preview_core = spawn_connecting_column_core(tile_props)
    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)
    return preview_core


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


def spawn_connecting_column_core(tile_props):
    """Return the column core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """

    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name
    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    core = draw_straight_wall_core(
        [tile_size[0],
         tile_size[1],
         tile_size[2] - base_size[2]],
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
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core
