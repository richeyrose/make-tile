import os
import bpy
from .. utils.registration import get_prefs
from .. lib.utils.vertex_groups import (
    get_verts_in_vert_group,
    get_vert_indexes_in_vert_group)


def load_materials(directory_path, blend_filenames):
    materials = []
    for filename in blend_filenames:
        file_path = os.path.join(directory_path, filename)
        materials.extend(get_materials_from_file(file_path))
    return materials


def get_blend_filenames(directory_path):
    blend_filenames = []
    if os.path.exists(directory_path):
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


def load_secondary_material():
    '''Adds a blank material to the passed in object'''
    prefs = get_prefs()
    secondary_mat = prefs.secondary_material
    if secondary_mat not in bpy.data.materials:
        secondary_mat = bpy.data.materials.new("Blank_Material")
    else:
        secondary_mat = bpy.data.materials['secondary_mat']
    return secondary_mat


def get_material_index(obj, material):
    material_index = list(obj.material_slots.keys()).index(material.name)
    return material_index


def assign_mat_to_vert_group(vert_group, obj, material):
    """Assigns the passed in material to the passed in vertex group.

    Args:
        vert_group (bpy.types.VertexGroup): vertex group
        obj (bpy.types.Object): Owning object
        material (bpy.types.Material): material
    """
    vert_group = get_vert_indexes_in_vert_group(vert_group, obj)
    material_index = get_material_index(obj, material)
    for poly in obj.data.polygons:
        count = 0
        for vert in poly.vertices:
            if vert in vert_group:
                count += 1
        if count == len(poly.vertices):
            poly.material_index = material_index


def get_vert_group_material(vert_group, obj):
    """Return the material assigned to the passed in vertex group.

    Args:
        vert_group (bpy.types.VertexGroup): vertex group
        obj (bpy.types.Object): Owning object

    Returns:
        bpy.types.Material: material
    """
    vert_group = get_vert_indexes_in_vert_group(vert_group.name, obj)
    for poly in obj.data.polygons:
        count = 0
        for vert in poly.vertices:
            if vert in vert_group:
                count += 1
        if count == len(poly.vertices):
            return obj.material_slots[poly.material_index].material


def add_preview_mesh_subsurf(obj):
    '''Adds an adaptive subdivison modifier'''
    obj_subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    obj_subsurf.subdivision_type = 'SIMPLE'
    obj_subsurf.levels = 0
    obj.cycles.use_adaptive_subdivision = True
    bpy.context.scene.cycles.preview_dicing_rate = 1


def update_displacement_material_2(obj, primary_material_name):
    primary_material = bpy.data.materials[primary_material_name]
    obj['primary_material'] = primary_material
    obj.data.materials.append(primary_material)


def update_preview_material_2(obj, primary_material_name):
    textured_groups = obj['textured_groups']

    primary_material = bpy.data.materials[primary_material_name]
    obj['primary_material'] = primary_material
    secondary_material = obj['secondary_material']
    obj.data.materials.append(secondary_material)
    obj.data.materials.append(primary_material)

    # for some reason the bools stored in our dict have been converted to ints /\0/\
    for key, value in textured_groups.items():
        if value is 1 or value is True:
            assign_mat_to_vert_group(key, obj, primary_material)


def assign_displacement_materials(obj, vert_group='None'):
    '''Keyword Arguments:
    obj - bpy.types.Object
    image_isize = [float, float]
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    '''
    # create new displacement modifier
    obj_disp_mod = obj.modifiers.new('Displacement', 'DISPLACE')
    obj_disp_mod.strength = 0
    obj_disp_mod.texture_coords = 'UV'
    obj_disp_mod.direction = 'NORMAL'
    obj_disp_mod.mid_level = 0
    obj_disp_mod.show_render = False
    if vert_group is not 'None':
        obj_disp_mod.vertex_group = vert_group

    # Create texture for this displacement modifier
    obj_disp_texture = bpy.data.textures.new(obj.name + '.texture', 'IMAGE')
    props = obj.mt_object_props
    props.disp_texture = obj_disp_texture
    props.disp_mod_name = obj_disp_texture.name


def assign_preview_materials(obj, primary_material, secondary_material, textured_vertex_groups):
    '''Keyword Arguments:
    obj - bpy.types.Object
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    textured_vertex_groups - [str]
    '''

    if secondary_material.name not in obj.data.materials:
        obj.data.materials.append(secondary_material)

    if primary_material.name not in obj.data.materials:
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
