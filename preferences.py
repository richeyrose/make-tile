# based on DECALmachine # 
import os
import shutil
import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from . utils.registration import get_path
from . utils.system import makedir, abspath
from . enums.enums import tile_systems, units


class MT_MakeTilePreferences(bpy.types.AddonPreferences):
    '''contains methods and properties for setting addon preferences'''

    bl_idname = __package__
    path = get_path()

    # asset libraries
    def update_assetspath(self, context):
        '''method to update the asset path'''
        if self.avoid_update:
            self.avoid_update = False
            return

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
            self. old_path = new_path

            # ensure the chosen assets_path is absolute
            self.avoid_update = True
            self.assets_path = new_path

            # reload assets
            reload_asset_libraries()

    assets_path: StringProperty(
        name="Assets Libraries",
        description="Path to Assets Libraries",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets"),
        update=update_assetspath
    )

    old_path: StringProperty(
        name="Old Path",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets")
    )

    default_units: EnumProperty(
        items=units,
        description="Units to use",
        name="Tile Units",
        default="IMPERIAL"
    )
    default_tile_system: EnumProperty(
        items=tile_systems,
        description="Default tile system to use",
        name="Tile System",
        default="OPENLOCK",
    )

    default_base_system: EnumProperty(
        items=tile_systems,
        description="Default base system to use",
        name="Base System",
        default="OPENLOCK",
    )

    default_bhas_base: BoolProperty(
        name="Seperate Base",
        description="Do walls, steps etc. have seperate bases",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.prop(self, 'assets_path')
        layout.prop(self, 'default_units')
        layout.prop(self, 'default_tile_system')
        layout.prop(self, 'default_base_system')
        layout.prop(self, 'default_bhas_base')
