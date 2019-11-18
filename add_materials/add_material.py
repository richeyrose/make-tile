import os
import bpy
from .. utils.registration import get_path
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_all, select, activate


def load_material(material):
    material_file = material + ".blend"
    materials_path = os.path.join(get_path(), "assets", "materials", material_file)
    with bpy.data.libraries.load(materials_path) as (data_from, data_to):
        data_to.materials = [material]
    material = data_to.materials[0]
    return material


def add_blank_material(obj):
    '''Adds a blank material to the passed in object'''
    if "Blank_Material" not in bpy.data.materials:
        blank_material = bpy.data.materials.new("Blank_Material")
    else:
        blank_material = bpy.data.materials['Blank_Material']
    obj.data.materials.append(blank_material)


def assign_mat_to_vert_group(vert_group, obj, mat):
    mode('EDIT')
    deselect_all()
    bpy.ops.object.vertex_group_set_active(group=vert_group)
    bpy.ops.object.vertex_group_select()
    material_index = list(obj.material_slots.keys()).index(mat)
    obj.active_material_index = material_index
    bpy.ops.object.material_slot_assign()
    mode('OBJECT')
