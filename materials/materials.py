import os
import bpy
from .. utils.registration import get_path, get_prefs
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_all, select, activate


def load_materials(directory_path, blend_filenames):
    for filename in blend_filenames:
        file_path = os.path.join(directory_path, filename)
        materials = get_materials_from_file(file_path)


def get_blend_filenames(directory_path):
    blend_filenames = [name for name in os.listdir(directory_path)
                       if name.endswith('.blend')]
    return blend_filenames


def get_materials_from_file(file_path):
    unique_materials = []
    with bpy.data.libraries.load(file_path) as (data_from, data_to):
        i = 0
        for material in data_from.materials:
            if material not in bpy.data.materials:
                unique_materials.append(data_from.materials[i])
            i += 1
        data_to.materials = unique_materials
    return data_to.materials


# TODO: Change this so get to choose what secondary material to load
def load_secondary_material():
    '''Adds a blank material to the passed in object'''
    if "Blank_Material" not in bpy.data.materials:
        blank_material = bpy.data.materials.new("Blank_Material")
    else:
        blank_material = bpy.data.materials['Blank_Material']
    return blank_material


def assign_mat_to_vert_group(vert_group, obj, material):
    # TODO: Replace with low level version as sloooooooow
    # https://blender.stackexchange.com/questions/69166/set-material-of-a-vertex-group-of-a-certain-face?rq=1
    '''
    Assigns the passed in material to the object's Vertex group
    Keyword arguments   -- vert_group (str) Vertex group
                        -- obj (bpy.types.Object)
                        -- material (bpy.types.Material)
    '''
    mode('OBJECT')
    deselect_all()
    activate(obj.name)
    mode('EDIT')
    deselect_all()
    bpy.ops.object.vertex_group_set_active(group=vert_group)
    bpy.ops.object.vertex_group_select()
    material_index = list(obj.material_slots.keys()).index(material.name)
    obj.active_material_index = material_index
    bpy.ops.object.material_slot_assign()
    mode('OBJECT')


def add_preview_mesh_modifiers(obj):
    obj_subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    obj_subsurf.subdivision_type = 'SIMPLE'
    obj_subsurf.levels = bpy.context.scene.mt_cycles_subdivision_quality


def add_displacement_mesh_modifiers_2(obj, image_size):
    obj_subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    obj_subsurf.subdivision_type = 'SIMPLE'
    obj_subsurf.levels = 0

    obj_disp_mod = obj.modifiers.new('Displacement', 'DISPLACE')
    obj_disp_mod.strength = 0
    obj_disp_mod.texture_coords = 'UV'
    obj_disp_mod.direction = 'NORMAL'
    obj_disp_mod.mid_level = 0

    obj_triangulate_mod = obj.modifiers.new('Triangulate', 'TRIANGULATE')

    obj_disp_texture = bpy.data.textures.new(obj.name + '.texture', 'IMAGE')
    obj['disp_texture'] = obj_disp_texture
    obj['subsurf_mod_name'] = obj_subsurf.name
    obj['disp_mod_name'] = obj_disp_mod.name


def update_displacement_material_2(obj, primary_material_name):
    for material in obj.data.materials:
        obj.data.materials.pop(index=0)

    primary_material = bpy.data.materials[primary_material_name]
    obj['primary_material'] = primary_material
    obj.data.materials.append(primary_material)


def update_preview_material_2(obj, primary_material_name):
    # get rid of existing materials
    for material in obj.data.materials:
        obj.data.materials.pop(index=0)

    textured_groups = obj['textured_groups']

    primary_material = bpy.data.materials[primary_material_name]
    obj['primary_material'] = primary_material
    secondary_material = obj['secondary_material']
    obj.data.materials.append(secondary_material)
    obj.data.materials.append(primary_material)

    # for some reason the bools stored in our dict haver been converted to ints /\0/\
    for key, value in textured_groups.items():
        if value is 1 or value is True:
            assign_mat_to_vert_group(key, obj, primary_material)


def assign_displacement_materials(obj, image_size, primary_material, secondary_material):
    '''Keyword Arguments:
    obj - bpy.types.Object
    image_isize = [float, float]
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    '''
    for material in obj.data.materials:
        obj.data.materials.pop(index=0)

    obj['primary_material'] = primary_material
    add_displacement_mesh_modifiers_2(obj, image_size)
    obj.data.materials.append(primary_material)


def assign_preview_materials(obj, primary_material, secondary_material, textured_vertex_groups):
    '''Keyword Arguments:
    obj - bpy.types.Object
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    textured_vertex_groups - [str]
    '''
    for material in obj.data.materials:
        obj.data.materials.pop(index=0)

    add_preview_mesh_modifiers(obj)

    obj.data.materials.append(secondary_material)
    obj.data.materials.append(primary_material)

    for group in textured_vertex_groups:
        assign_mat_to_vert_group(group, obj, primary_material)


def assign_texture_to_areas(obj, primary_material, secondary_material):
    '''Keyword Arguments:
    obj - bpy.types.Object
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    '''
    material_slots = obj.material_slots
    all_vert_groups = obj.vertex_groups
    textured_vert_groups = obj.mt_textured_areas_coll

    if secondary_material not in material_slots:
        obj.data.materials.append(bpy.data.materials[secondary_material])
    if primary_material not in material_slots:
        obj.data.materials.append(bpy.data.materials[primary_material])

    for group in textured_vert_groups:
        if group.value is False:
            assign_mat_to_vert_group(group.name, obj, bpy.data.materials[secondary_material])
        else:
            assign_mat_to_vert_group(group.name, obj, bpy.data.materials[primary_material])
