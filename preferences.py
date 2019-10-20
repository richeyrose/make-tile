# based on DECALmachine # 
import os
import shutil
import bpy
from bpy.props import StringProperty
from . utils.registration import get_path
from . utils.system import makedir, abspath

class MT_MakeTilePreferences(bpy.types.AddonPreferences):
    '''contains methods and properties for setting addon preferences'''

    bl_idname = __package__
    path = get_path()

    #asset libraries
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

            #set the new old_path
            self. old_path = new_path

            # ensure the chosen assets_path is absolute
            self.avoid_update = True
            self.assets_path = new_path

            # reload assets
            reload_asset_libraries()

    assets_path: StringProperty(
        name="Assets Libraries",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets"),
        update=update_assetspath
        )

    old_path: StringProperty(
        name="Old Path",
        subtype='DIR_PATH',
        default=os.path.join(path, "assets")
        )
        
    def draw(self, context):
        layout = self.layout
        layout.label(text='Assets Path')
        row = layout.row()
        row.prop(self, 'assets_path')
