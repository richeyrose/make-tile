import os
from math import radians
from mathutils import Vector
import bpy

from bpy.types import Operator, Panel
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)

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
    create_common_tile_props)


class MT_PT_Roof_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Roof_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "ROOF"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")

        layout.prop(scene_props, 'roof_type', text="Roof Type")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Roof Properties")
        layout.prop(scene_props, 'tile_z', text="Apex Height")
        layout.prop(scene_props, 'tile_x', text="Roof Width")
        layout.prop(scene_props, "tile_y", text="Roog Length")

        layout.prop(scene_props, 'end_eaves_pos', text="Positive End Eaves")
        layout.prop(scene_props, 'end_eaves_neg', text="Negative End Eaves")
        layout.prop(scene_props, 'side_eaves', text="Side Eaves")

        layout.prop(scene_props, 'base_z', text="Base Height")

        layout.prop(scene_props, 'subdivision_density', text="Subdivision Density")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Roof(MT_Tile_Generator, Operator):
    """Operator. Generates a roof tile."""

    bl_idname = "object.make_roof"
    bl_label = "Roof"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "ROOF"

    def execute(self, context):
        """Execute the Operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint

        cursor_orig_loc, cursor_orig_rot = initialise_roof_creator(
            context,
            scene_props)

        subclasses = get_all_subclasses(MT_Tile_Generator)

        gable = spawn_prefab(context, subclasses, base_blueprint, 'ROOF_GABLE')
        top = spawn_prefab(context, subclasses, 'OPENLOCK', 'S_ROOF_TOP')


        # finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        return {'FINISHED'}


class MT_OT_Make_Openlock_Roof_Gable(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof gable."""

    bl_idname = "object.make_openlock_roof_gable"
    bl_label = "Roof Gable"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "ROOF_GABLE"

    def execute(self, context):
        """Execute the operator."""
        return{'FINISHED'}


class MT_OT_Make_Openlock_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock Roof Top."""

    bl_idname = "object.make_openlock_roof_top"
    bl_label = "Roof Top"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        return{'FINISHED'}


def initialise_roof_creator(context, scene_props):
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    create_collection('Roofs', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Roofs'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.roof_type = scene_props.roof_type
    tile_props.end_eaves_pos = scene_props.end_eaves_pos
    tile_props.end_eaves_neg = scene_props.end_eaves_neg
    tile_props.side_eaves = scene_props.side_eaves
    tile_props.tile_type = 'ROOF'

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.tile_x, scene_props.tile_y, scene_props.base_z)
    tile_props.subdivision_density = scene_props.subdivision_density
    tile_props.displacement_thickness = scene_props.displacement_thickness

    return cursor_orig_loc, cursor_orig_rot
