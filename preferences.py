import os
import shutil
import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    CollectionProperty,
    PointerProperty)
from . utils.registration import get_path
from . utils.system import makedir, abspath
from . enums.enums import tile_blueprints, units
from .tile_creation.create_tile import (
    create_tile_type_enums,
    create_base_blueprint_enums,
    create_main_part_blueprint_enums)


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

    load_user_materials_on_startup: BoolProperty(
        default=False,
        name="Load User Materials on Startup?",
        description="Whether to load user materials on startup so they appear in the material list when generating a new tile."
    )

    default_materials: CollectionProperty(
        name="Default Materials",
        type=MT_DefaultMaterial)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'user_assets_path')
        layout.prop(self, 'default_export_path')
        layout.prop(self, 'default_units')
        layout.label(text="Default Materials")
        layout.prop(self, 'default_materials')
        layout.prop(self, 'load_user_materials_on_startup')

# TODO: Stub - reload_asset_libraries


def reload_asset_libraries():
    print('reload_asset_libraries')
