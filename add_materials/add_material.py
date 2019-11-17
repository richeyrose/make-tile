import os
import bpy
from .. utils.registration import get_path


def add_material(axes, obj, material):
    mat = load_material(material)
    obj.data.materials.append(mat)


def load_material(material):
    material_file = material + ".blend"
    materials_path = os.path.join(get_path(), "assets", "materials", material_file)
    with bpy.data.libraries.load(materials_path) as (data_from, data_to):
        data_to.materials = [material]
    material = data_to.materials[0]
    return material
