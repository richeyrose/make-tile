import os
import shutil
import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from . utils.registration import get_path
from . utils.system import makedir, abspath
from . enums.enums import tile_main_systems, base_systems, tile_blueprints, units


class MT_MakeTilePreferences(bpy.types.AddonPreferences):
    '''contains methods and properties for setting addon preferences'''

    bl_idname = __package__
    path = get_path()
    user_path = os.path.expanduser('~')
    export_path = os.path.join(user_path, 'MakeTile')

    # asset libraries
    def update_assetspath(self, context):
        '''method to update the asset path'''
        ''''Based on DECALMachine'''

        new_path = makedir(abspath(self.assets_path))
        old_path = abspath(self.old_path)

        if new_path != old_path:
            print(" » Copying asset libraries from %s to %s" % (old_path, new_path))

            libs = sorted([f for f in os.listdir(old_path) if os.path.isdir(os.path.join(old_path, f))])

            for lib in libs:
                src = os.path.join(old_path, lib)
                dest = os.path.join(new_path, lib)

                if not os.path.exists(dest):
                    print(" » %s" % (lib))
                    shutil.copytree(src, dest)

            # set the new old_path
            self.old_path = new_path

            # reload assets
            reload_asset_libraries()


    assets_path: StringProperty(
        name="Assets Libraries",
        description="Path to Assets Libraries",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets"),
        update=update_assetspath
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
        items=tile_main_systems,
        description="Default tile system to use for main part of tile for custom tiles",
        name="Tile System",
        default="OPENLOCK",
    )

    default_base_system: EnumProperty(
        items=base_systems,
        description="Default base system to use for custom tiles",
        name="Base System",
        default="OPENLOCK",
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.prop(self, 'assets_path')
        layout.prop(self, 'default_export_path')
        layout.prop(self, 'default_units')
        layout.prop(self, 'default_tile_blueprint')
        layout.prop(self, 'default_tile_main_system')
        layout.prop(self, 'default_base_system')
        layout.prop(self, 'secondary_material')


# TODO: Stub - reload_asset_libraries
def reload_asset_libraries():
    print('reload_asset_libraries')
