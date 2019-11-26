import os
import bpy
from . utils.registration import get_prefs
from . utils.registration import get_path
from . materials.materials import load_materials, get_blend_filenames


class MPT_OT_Import_materials(bpy.types.Operator):
    bl_idname = "scene.import_materials"
    bl_label = "Import Materials"

    def execute(self, context):

        materials_path = os.path.join(get_path(), "assets", "materials")
        material_filenames = get_blend_filenames(materials_path)
        materials = load_materials(materials_path, material_filenames)
        for material in materials:
            print(material.name)

    return {'FINISHED'}