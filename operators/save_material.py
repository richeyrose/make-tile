import os
import bpy
from .. utils.registration import get_path, get_prefs
from .. materials.materials import get_blend_filenames, get_materials_from_file


class MT_OT_Export_Material(bpy.types.Operator):
    '''Exports the active material to an external library .blend file'''
    bl_idname = "material.mt_export_material"
    bl_label = "Export Material"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'

    def execute(self, context):
        prefs = get_prefs()
        materials_path = os.path.join(prefs.assets_path, "materials")
        filepath = os.path.join(materials_path, 'user_material_library.blend')

        if os.path.isfile(filepath) is True:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.materials = data_from.materials
            data_to.materials.append(context.object.active_material)
            data_blocks = {*data_to.materials}
        else:
            data_blocks = {context.object.active_material}
        bpy.data.libraries.write(filepath, data_blocks, fake_user=True)

        return {'FINISHED'}
