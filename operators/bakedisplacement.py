'''contains operator class for baking displacement maps to tiles'''
import bpy
from .. materials.materials import load_secondary_material, assign_mat_to_vert_group, assign_displacement_materials
from .. lib.utils.selection import deselect_all, select_all, select, activate
from .. lib.utils.utils import mode
from .. lib.utils.vertex_groups import get_selected_face_indices, assign_material_to_faces
from .. utils.registration import get_prefs


class MT_OT_Assign_Material_To_Vert_Group(bpy.types.Operator):
    """Assigns the selected material to the selected vertex group"""
    bl_idname = "object.assign_mat_to_active_vert_group"
    bl_label = "Assign Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        prefs = get_prefs()
        obj = context.object

        object_props = obj.mt_object_props
        mat_name = context.scene.mt_tile_material_1
        material = bpy.data.materials[mat_name]
        vertex_group = obj.vertex_groups.active.name
        primary_material = bpy.data.materials[mat_name]
        secondary_material = bpy.data.materials[prefs.secondary_material]
        image_size = bpy.context.scene.mt_tile_resolution

        # check that material is on our object and add it if not
        if mat_name in obj.material_slots.keys():
            assign_mat_to_vert_group(vertex_group, obj, material)
        else:
            if len(obj.material_slots) == 0:  # check to make sure we have a material applied already otherwise material will be applied to whole object
                obj.data.materials.append(secondary_material)
            obj.data.materials.append(primary_material)
            assign_mat_to_vert_group(vertex_group, obj, material)

        # create new displacement material item and save it on our displacement object
        disp_obj = object_props.linked_object
        item = disp_obj.mt_object_props.disp_materials_collection.add()
        item.material = primary_material
        return {'FINISHED'}


class MT_OT_Remove_Material_From_Vert_Group(bpy.types.Operator):
    """Removes primary material from the selected vertex group
    and assigns secondary material to it"""
    bl_idname = "object.remove_mat_from_active_vert_group"
    bl_label = "Remove Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        prefs = get_prefs()
        obj = context.object
        vertex_group = obj.vertex_groups.active.name
        secondary_material = bpy.data.materials[prefs.secondary_material]

        if prefs.secondary_material in obj.material_slots.keys():
            assign_mat_to_vert_group(vertex_group, obj, secondary_material)
        else:
            obj.data.materials.append(secondary_material)
            assign_mat_to_vert_group(vertex_group, obj, secondary_material)

        return {'FINISHED'}


class MT_OT_Bake_Displacement(bpy.types.Operator):
    """Bakes the preview material to a displacement map so it becomes 3D"""
    bl_idname = "scene.bake_displacement"
    bl_label = "Bake a displacement map"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        preview_obj = bpy.context.object
        disp_obj = preview_obj.mt_object_props.linked_object
        disp_mat_coll = disp_obj.mt_object_props.disp_materials_collection

        resolution = context.scene.mt_tile_resolution
        disp_obj.hide_viewport = False
        disp_image = bake_displacement_map(disp_obj, resolution)

        disp_texture = disp_obj['disp_texture']
        disp_texture.image = disp_image
        disp_mod = disp_obj.modifiers[disp_obj['disp_mod_name']]
        disp_mod.texture = disp_texture
        disp_mod.mid_level = 0
        disp_mod.strength = 0.1
        subsurf_mod = disp_obj.modifiers[disp_obj['subsurf_mod_name']]

        subsurf_mod.levels = bpy.context.scene.mt_subdivisions

        preview_obj.hide_viewport = True

        return {'FINISHED'}


def bake_displacement_map(disp_obj, resolution):
    prefs = get_prefs()
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
    bpy.context.scene.render.tile_x = resolution
    bpy.context.scene.render.tile_y = resolution
    bpy.context.scene.cycles.bake_type = 'EMIT'

    disp_image = bpy.data.images.new(disp_obj.name + '.image', width=1024, height=1024)
    disp_mat_coll = disp_obj.mt_object_props.disp_materials_collection

    for item in disp_mat_coll:
        material = item.material
        # plug emission node into output for baking
        tree = material.node_tree
        mat_output_node = tree.nodes['Material Output']
        displacement_emission_node = tree.nodes['disp_emission']
        tree.links.new(displacement_emission_node.outputs['Emission'], mat_output_node.inputs['Surface'])

        # sever displacement node link because otherwise it screws up baking
        displacement_node = tree.nodes['final_disp']
        link = displacement_node.outputs[0].links[0]
        tree.links.remove(link)

        # save displacement strength
        strength_node = tree.nodes['Strength']

        if 'disp_dir' in disp_obj:
            if disp_obj['disp_dir'] == 'neg':
                disp_obj['disp_strength'] = -strength_node.outputs[0].default_value
            else:
                disp_obj['disp_strength'] = strength_node.outputs[0].default_value
        else:
            disp_obj['disp_strength'] = strength_node.outputs[0].default_value

        # assign image to image node
        texture_node = tree.nodes['disp_texture_node']
        texture_node.image = disp_image

    # project from preview to displacement mesh when baking
    preview_mesh = disp_obj.mt_object_props.linked_object
    deselect_all()
    select(preview_mesh.name)
    select(disp_obj.name)
    activate(disp_obj.name)
    bpy.context.scene.render.bake.use_selected_to_active = True
    bpy.context.scene.render.bake.cage_extrusion = 1

    # temporarily assign a displacement material so we can bake to an image
    for material in disp_obj.data.materials:
        disp_obj.data.materials.pop(index=0)
    disp_obj.data.materials.append(disp_mat_coll[0].material)

    # bake
    bpy.ops.object.bake(type='EMIT')

    # pack image
    disp_image.pack()

    # reset shaders
    for item in disp_mat_coll:
        material = item.material
        tree = material.node_tree
        surface_shader_node = tree.nodes['surface_shader']
        displacement_node = tree.nodes['final_disp']
        mat_output_node = tree.nodes['Material Output']
        tree.links.new(surface_shader_node.outputs['BSDF'], mat_output_node.inputs['Surface'])
        tree.links.new(displacement_node.outputs['Displacement'], mat_output_node.inputs['Displacement'])

    # TODO: This is really hacky. get rid and do it properly when
    #  you make a decent secondary material
    # remove displacement material and add secondary material
    for material in disp_obj.data.materials:
        disp_obj.data.materials.pop(index=0)
    disp_obj.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # reset engine
    bpy.context.scene.cycles.samples = orig_samples
    bpy.context.scene.render.tile_x = orig_x
    bpy.context.scene.render.tile_y = orig_y
    bpy.context.scene.cycles.bake_type = orig_bake_type
    bpy.context.scene.render.engine = orig_engine

    return disp_image
