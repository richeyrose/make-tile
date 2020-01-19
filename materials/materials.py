import os
import bpy
from .. utils.registration import get_path, get_prefs
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_all, select, activate
from .. lib.utils.vertex_groups import get_verts_in_vert_group, get_vert_indexes_in_vert_group


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


def load_secondary_material():
    '''Adds a blank material to the passed in object'''
    prefs = get_prefs
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
    vert_group = get_vert_indexes_in_vert_group(vert_group, obj)
    material_index = get_material_index(obj, material)
    poly_list = []
    for poly in obj.data.polygons:
        count = 0
        for vert in poly.vertices:
            if vert in vert_group:
                count += 1
        if count == len(poly.vertices):
            poly.material_index = material_index


def add_preview_mesh_subsurf(obj):
    '''Adds a triangulate modifier so that sockets etc. appear correctly
    then adds an adaptive subdivison modifier'''

    obj_triangulate = obj.modifiers.new('Triangulate', 'TRIANGULATE')

    obj_subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    obj_subsurf.subdivision_type = 'SIMPLE'
    obj_subsurf.levels = bpy.context.scene.mt_cycles_subdivision_quality
    obj.cycles.use_adaptive_subdivision = True
    bpy.context.scene.cycles.preview_dicing_rate = 1

    if 'Camera' in bpy.data.objects:
        bpy.context.scene.cycles.dicing_camera = bpy.data.objects['Camera']


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

    # create new displacement modifier
    obj_disp_mod = obj.modifiers.new('Displacement', 'DISPLACE')
    obj_disp_mod.strength = 0
    obj_disp_mod.texture_coords = 'UV'
    obj_disp_mod.direction = 'NORMAL'
    obj_disp_mod.mid_level = 0

    # Create texture for this displacement modifier
    obj_disp_texture = bpy.data.textures.new(obj.name + '.texture', 'IMAGE')
    obj['disp_texture'] = obj_disp_texture
    obj['disp_mod_name'] = obj_disp_mod.name

    obj.data.materials.append(secondary_material)
    obj.data.materials.append(primary_material)

    # create new displacement material item and save it on our displacement object
    item = obj.mt_object_props.disp_materials_collection.add()
    item.material = primary_material
    item.disp_texture = obj_disp_texture
    item.disp_mod_name = obj_disp_mod.name


def assign_preview_materials(obj, primary_material, secondary_material, textured_vertex_groups):
    '''Keyword Arguments:
    obj - bpy.types.Object
    primary_material - bpy.types.Material
    secondary_material - bpy.types.Material
    textured_vertex_groups - [str]
    '''
    for material in obj.data.materials:
        obj.data.materials.pop(index=0)

    # add_preview_mesh_subsurf(obj)

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
