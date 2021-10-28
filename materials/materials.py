import os
import bpy
from pathlib import Path
from .. utils.registration import get_prefs
from ..lib.utils.utils import slugify
from ..lib.utils.file_handling import find_and_rename
from .. lib.utils.vertex_groups import (
    get_verts_in_vert_group,
    get_vert_indexes_in_vert_group)


# def save_material_as_default(material):
#     """Write the passed in material to the default material library directory.

#     Args:
#         material (bpy.types.Material): Material
#     """
#     prefs = get_prefs()
#     default_assets_dir = os.path.join(prefs.assets_path, "materials")

#     # check if the material is a linked library file
#     if material.library:
#         # create a symbolic link to the material file in the default materials directpry
#         pass

#     # else save material to default materials directory
#     else:
#         # construct filename to avoid clashes
#         blends = [f for f in os.listdir(default_assets_dir) if os.path.isfile(
#             os.path.join(default_assets_dir, f)) and f.endswith(".blend")]
#         stems = [Path(blend).stem for blend in blends]
#         slug = material.name
#         filename = find_and_rename(slug, stems) + '.blend'

#         # write to file
#         filepath = os.path.join(default_assets_dir, filename)
#         bpy.data.libraries.write(filepath, {material}, fake_user=True)


def load_materials(filepath):
    """Load all materials in a file into the scene. Checks to see whether a material is unique first.

    Args:
        filepath (str): path to file containing materials.
    """
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.materials = data_from.materials

    for new_mat in data_to.materials:
        existing_mats = [mat for mat in bpy.data.materials if mat != new_mat]
        unique, matched = material_is_unique(new_mat, existing_mats)
        if not unique:
            bpy.data.materials.remove(new_mat)


def get_blend_filenames(directory_path):
    blend_filenames = []
    if os.path.exists(directory_path):
        blend_filenames = [name for name in os.listdir(directory_path)
                           if name.endswith('.blend')]
    return blend_filenames


def load_secondary_material():
    '''Adds a blank material to the passed in object.'''
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
    """Assign the passed in material to the passed in vertex group.

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
            assign_mat_to_vert_group(
                group.name, obj, bpy.data.materials[secondary_material])
        else:
            assign_mat_to_vert_group(
                group.name, obj, bpy.data.materials[primary_material])

# TODO Ensure this works for custom image material. I think we also need
# to check whether image is unique otherwise it won't work


def material_is_unique(material, materials):
    """Check whether the passed in material already exists.

    Parameters
    material : bpy.types.Material
        material to check for uniqueness
    materials[list]: List of bpy.types.Material
    Returns
    Boolean
        True if material is unique

    matched_material : bpy.types.Material
        Matching material. None if material is unique

    """
    found = []
    # slugify material name and strip digits
    mat_name = slugify(material.name.rstrip('0123456789. '))

    # check if material shares a name with another material (minus numeric suffix)
    for mat in materials:
        stripped_name = slugify(mat.name.rstrip('0123456789. '))
        if stripped_name == mat_name:
            found.append(mat)

    if len(found) == 0:
        return True, None

    # check if materials that share the same name share the same node tree by comparing names of nodes
    mat_node_keys = material.node_tree.nodes.keys()

    found_2 = []
    for mat in found:
        found_mat_node_keys = mat.node_tree.nodes.keys()
        if mat_node_keys.sort() == found_mat_node_keys.sort():
            found_2.append(mat)

    if len(found_2) == 0:
        return True, None

    # check if all nodes of type 'VALUE' have the same default values on their outputs
    mat_node_values = []
    for node in material.node_tree.nodes:
        if node.type == 'VALUE':
            mat_node_values.append(node.outputs[0].default_value)

    for mat in found_2:
        found_mat_node_values = []
        for node in mat.node_tree.nodes:
            if node.type == 'VALUE':
                found_mat_node_values.append(node.outputs[0].default_value)
        if mat_node_values.sort() == found_mat_node_values.sort():
            return False, mat

    return True, None
