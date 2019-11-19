import os
import bpy
from .. utils.registration import get_path
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_all, select, activate


def load_material(material):
    '''loads a material into the scene from external blend file'''
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
    return blank_material


def assign_mat_to_vert_group(vert_group, obj, material):
    mode('EDIT')
    deselect_all()
    bpy.ops.object.vertex_group_set_active(group=vert_group)
    bpy.ops.object.vertex_group_select()
    material_index = list(obj.material_slots.keys()).index(material)
    obj.active_material_index = material_index
    bpy.ops.object.material_slot_assign()
    mode('OBJECT')


def bake_displacement_map(material, obj):
    # save original settings
    orig_engine = bpy.context.scene.render.engine
    # cycles settings
    orig_samples = bpy.context.scene.cycles.samples
    orig_x = bpy.context.scene.render.tile_x
    orig_y = bpy.context.scene.render.tile_y
    orig_bake_type = bpy.context.scene.cycles.bake_type

    # switch to Cycles and set up rendering settings for baking
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 1
    bpy.context.scene.render.tile_x = 2048
    bpy.context.scene.render.tile_y = 2048
    bpy.context.scene.cycles.bake_type = 'EMIT'

    # plug emission node into output for baking
    tree = material.node_tree
    mat_output_node = tree.nodes['Material Output']
    displacement_emission_node = tree.nodes['disp_emission']
    tree.links.new(displacement_emission_node.outputs['Emission'], mat_output_node.inputs['Surface'])

    # bake
    bpy.ops.object.bake(type='EMIT')

    # reset shader
    surface_shader_node = tree.nodes['surface_shader']
    tree.links.new(surface_shader_node.outputs['BSDF'], mat_output_node.inputs['Surface'])

    # reset engine
    bpy.context.scene.cycles.samples = orig_samples
    bpy.context.scene.render.tile_x = orig_x
    bpy.context.scene.render.tile_y = orig_y
    bpy.context.scene.cycles.bake_type = orig_bake_type
    bpy.context.scene.render.engine = orig_engine
    
