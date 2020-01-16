import os
import bpy
from .. utils.registration import get_path, get_prefs
from .. materials.materials import get_blend_filenames


class MT_OT_Export_Material(bpy.types.Operator):
    '''Exports the currently selected maketile material to an external library .blend file'''
    bl_idname = "scene.export_material"
    bl_label = "Export Material"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'

    def execute(self, context):
        prefs = get_prefs()
        materials_path = os.path.join(prefs.assets_path, "materials")

        filepath = os.path.join(materials_path, 'material_library.blend')
        material = bpy.data.materials[context.scene.mt_tile_material_1]
        data_blocks = {material}
        bpy.data.libraries.write(filepath, data_blocks, fake_user=True)

        return {'FINISHED'}
