import os
import shutil
import bpy
from bpy.types import PropertyGroup, Operator
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    CollectionProperty,
    PointerProperty,
    IntProperty)

from . utils.registration import get_path
from . utils.system import makedir, abspath
from . enums.enums import tile_blueprints, units
from .tile_creation.create_tile import (
    create_tile_type_enums,
    create_base_blueprint_enums,
    create_main_part_blueprint_enums)
from .utils.registration import get_prefs
from .app_handlers import create_default_materials


class MT_DefaultMaterial(PropertyGroup):
    name: StringProperty(
        name="Name",
        default=""
    )

    filepath: StringProperty(
        name="File Path",
        subtype="FILE_PATH"
    )


class MT_MakeTilePreferences(bpy.types.AddonPreferences):
    '''contains methods and properties for setting addon preferences'''
    bl_idname = __package__
    path = get_path()
    user_path = os.path.expanduser('~')
    export_path = os.path.join(user_path, 'MakeTile')
    user_assets_path = os.path.join(user_path, 'MakeTile')

    assets_path: StringProperty(
        name="Default Asset Libraries",
        description="Path to Default Asset Libraries",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets")
    )

    user_assets_path: StringProperty(
        name="User Asset Libraries",
        subtype='DIR_PATH',
        description="Path to User Asset Libraries",
        default=user_assets_path,
    )

    secondary_material: StringProperty(
        name="Secondary Material",
        default="Plastic"
    )

    default_export_path: StringProperty(
        name="Export Path",
        subtype='DIR_PATH',
        description="Default folder to export tiles to",
        default=export_path,
    )

    old_path: StringProperty(
        name="Old Path",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets")
    )

    default_units: EnumProperty(
        items=units,
        description="Default units to use",
        name="Tile Units",
        default="INCHES"
    )

    default_tile_blueprint: EnumProperty(
        items=tile_blueprints,
        description="Default blueprint to use",
        name="Tile Blueprint",
        default="OPENLOCK",
    )

    default_tile_main_system: EnumProperty(
        items=create_main_part_blueprint_enums,
        description="Default tile system to use for main part of tile for custom tiles",
        name="Default Tile System"
    )

    default_base_system: EnumProperty(
        items=create_base_blueprint_enums,
        description="Default base system to use for custom tiles",
        name="Default Base System"
    )

    default_tile_type: EnumProperty(
        items=create_tile_type_enums,
        name="Default Tile Type"
    )

    default_materials: CollectionProperty(
        name="Default Materials",
        type=MT_DefaultMaterial)

    default_mat_behaviour: EnumProperty(
        name="Default Material Behaviour",
        description="Append linked materials on tile generation?",
        items=[
            ("APPEND", "Append", "Append the material and make a local copy."),
            ("LINK", "Link", "Link to the material.")],
        default="APPEND"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'user_assets_path')
        layout.prop(self, 'default_export_path')
        layout.prop(self, 'default_units')
        layout.prop(self, 'default_mat_behaviour')
        layout.label(text="Default Materials:")
        # Draw list of default materials
        i = 0
        for mat in self.default_materials:
            row = layout.row()
            row.label(text=mat.name)
            row.label(text=mat.filepath)
            op = row.operator('addons.mt_remove_mat_from_defaults')
            op.material = mat.name
            op.filepath = mat.filepath
            op.index = i
            i += 1
        layout.operator('addons.mt_restore_default_materials')

        op = layout.operator('addons.mt_add_active_mat_to_defaults')


class MT_OT_Restore_Default_Materials(Operator):
    bl_idname = "addons.mt_restore_default_materials"
    bl_label = "Restore Default Materials"
    bl_description = "Restore Default MakeTile materials."

    def execute(self, context):
        create_default_materials(context)
        self.report({'INFO'}, "Default materials restored.")
        return {'FINISHED'}


class MT_OT_Add_Active_Material_To_Defaults(Operator):
    bl_idname = "addons.mt_add_active_mat_to_defaults"
    bl_label = "Add Active Material to Default List"
    bl_description = "Add active material to MakeTile default material list."

    @classmethod
    def poll(cls, context):
        return bpy.data.filepath and context.active_object.active_material

    def execute(self, context):
        prefs = get_prefs()
        default_mats = prefs.default_materials
        new_mat = default_mats.add()
        new_mat.name = context.active_object.active_material.name
        new_mat.filepath = bpy.data.filepath
        return {'FINISHED'}


class MT_OT_Remove_Material_From_Defaults(Operator):
    bl_idname = "addons.mt_remove_mat_from_defaults"
    bl_label = "Remove"
    bl_description = "Remove material from default material list."

    material: StringProperty(
        name="Material"
    )

    filepath: StringProperty(
        name="Filepath",
        subtype="FILE_PATH"
    )

    index: IntProperty(
        name="Index"
    )

    def execute(self, context):
        prefs = get_prefs()
        default_mats = prefs.default_materials
        default_mats.remove(self.index)
        self.report({'INFO'}, self.material +
                    " removed from default material list.")

        return {'FINISHED'}


# TODO: Stub - reload_asset_libraries


def reload_asset_libraries():
    print('reload_asset_libraries')
