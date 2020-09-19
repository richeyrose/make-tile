'''contains operator class for baking displacement maps to tiles'''
import bpy
from .. materials.materials import (
    assign_mat_to_vert_group,
    get_vert_group_material,
    get_material_index)
from .. lib.utils.vertex_groups import (
    get_verts_with_material,
    clear_vert_group)
from .. utils.registration import get_prefs


class MT_OT_Assign_Material_To_Vert_Group(bpy.types.Operator):
    """Assigns the active material to the selected vertex group"""
    bl_idname = "object.mt_assign_mat_to_active_vert_group"
    bl_label = "Assign Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        prefs = get_prefs()

        active_obj = context.active_object
        vert_group_name = active_obj.vertex_groups.active.name

        primary_material = context.object.active_material
        secondary_material = bpy.data.materials[prefs.secondary_material]

        selected_objects = context.selected_objects

        for obj in selected_objects:
            if primary_material.name not in obj.material_slots:
                obj.data.materials.append(primary_material)

            vert_groups = obj.vertex_groups
            if vert_group_name in vert_groups:
                # obj_props = obj.mt_object_props
                assign_mat_to_vert_group(vert_group_name, obj, primary_material)
                textured_verts = set()

                for key, value in obj.material_slots.items():
                    if key != secondary_material.name:
                        verts = get_verts_with_material(obj, key)
                        textured_verts = verts | textured_verts

                if 'disp_mod_vert_group' in obj.vertex_groups:
                    disp_vert_group = obj.vertex_groups['disp_mod_vert_group']
                    clear_vert_group(disp_vert_group, obj)
                    disp_vert_group.add(index=list(textured_verts), weight=1, type='ADD')
                else:
                    disp_vert_group = obj.vertex_groups.new(name='disp_mod_vert_group')
                    disp_vert_group.add(index=list(textured_verts), weight=1, type='ADD')

                '''
                # get disp objects
                disp_obj = obj_props.linked_object

                textured_verts = set()

                for key, value in obj.material_slots.items():
                    if key != secondary_material.name:
                        verts = get_verts_with_material(obj, key)
                        textured_verts = verts | textured_verts

                if 'disp_mod_vert_group' in disp_obj.vertex_groups:
                    disp_vert_group = disp_obj.vertex_groups['disp_mod_vert_group']
                    clear_vert_group(disp_vert_group, disp_obj)
                    disp_vert_group.add(index=list(textured_verts), weight=1, type='ADD')
                else:
                    disp_vert_group = obj.vertex_groups.new(name='disp_mod_vert_group')
                    disp_vert_group.add(index=list(textured_verts), weight=1, type='ADD')
                '''
        return {'FINISHED'}


class MT_OT_Remove_Material_From_Vert_Group(bpy.types.Operator):
    """Removes primary material from the selected vertex group
    and assigns secondary material to it"""
    bl_idname = "object.mt_remove_mat_from_active_vert_group"
    bl_label = "Remove Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        prefs = get_prefs()

        active_obj = context.active_object
        vert_group_name = active_obj.vertex_groups.active.name

        secondary_material = bpy.data.materials[prefs.secondary_material]

        selected_objects = context.selected_objects

        for obj in selected_objects:
            if secondary_material.name not in obj.material_slots:
                obj.data.materials.append(secondary_material)
            assign_mat_to_vert_group('disp_mod_vert_group', obj, secondary_material)
            vert_groups = obj.vertex_groups

            if vert_group_name in vert_groups:
                assign_mat_to_vert_group(vert_group_name, obj, secondary_material)


        return {'FINISHED'}


class MT_OT_Make_3D(bpy.types.Operator):
    """Bakes the preview material to a displacement map so it becomes 3D"""
    bl_idname = "scene.mt_make_3d"
    bl_label = "Bake a displacement map"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        selected_objects = context.selected_objects
        orig_render_settings = set_cycles_to_bake_mode()

        for obj in selected_objects:
            obj_props = obj.mt_object_props

            if obj_props.geometry_type == 'PREVIEW':
                preview_obj = obj
                tile = bpy.data.collections[obj_props.tile_name]
                # disp_obj = obj_props.linked_object
                disp_obj = preview_obj
                disp_strength = tile.mt_tile_props.displacement_strength
                #disp_obj.hide_viewport = False
                disp_image, disp_obj = bake_displacement_map(preview_obj, disp_obj)
                disp_texture = disp_obj['disp_texture']
                disp_texture.image = disp_image
                disp_mod = disp_obj.modifiers[disp_obj['disp_mod_name']]
                disp_mod.texture = disp_texture
                disp_mod.mid_level = 0
                disp_mod.strength = disp_strength
                #subsurf_mod = disp_obj.modifiers[disp_obj['subsurf_mod_name']]
                subsurf_mod = disp_obj.modifiers['Subsurf']
                subsurf_mod.levels = bpy.context.scene.mt_scene_props.subdivisions
                #preview_obj.hide_viewport = True
                obj_props.geometry_type = 'DISPLACEMENT'
        reset_renderer_from_bake(orig_render_settings)
        return {'FINISHED'}


def set_cycles_to_bake_mode():
    context = bpy.context
    resolution = context.scene.mt_scene_props.tile_resolution

    # save original settings
    cycles_settings = {
        'orig_engine': context.scene.render.engine,
        'orig_samples': context.scene.cycles.samples,
        'orig_x': context.scene.render.tile_x,
        'orig_y': context.scene.render.tile_y,
        'orig_bake_type': context.scene.cycles.bake_type
    }

    # switch to Cycles and set up rendering settings for baking
    context.scene.render.engine = 'CYCLES'
    context.scene.cycles.samples = 1
    context.scene.render.tile_x = resolution
    context.scene.render.tile_y = resolution
    context.scene.cycles.bake_type = 'EMIT'

    return cycles_settings


def reset_renderer_from_bake(orig_settings):
    context = bpy.context
    context.scene.cycles.samples = orig_settings['orig_samples']
    context.scene.render.tile_x = orig_settings['orig_x']
    context.scene.render.tile_y = orig_settings['orig_y']
    context.scene.cycles.bake_type = orig_settings['orig_bake_type']
    context.scene.render.engine = orig_settings['orig_engine']


def bake_displacement_map(preview_obj, disp_obj):
    context = bpy.context
    prefs = get_prefs()
    image_resolution = context.scene.mt_scene_props.tile_resolution
    disp_image = bpy.data.images.new(
        disp_obj.name + '.image',
        width=image_resolution,
        height=image_resolution,
        alpha=True,
        float_buffer=True,
        is_data=True
    )
    disp_image.file_format = 'OPEN_EXR'

    disp_materials = []
    mat_set = set()
    for item in preview_obj.material_slots.items():
        if item[0]:
            material = bpy.data.materials[item[0]]
            tree = material.node_tree

            if 'disp_emission' in tree.nodes and material not in mat_set:
                # plug emission node into output for baking
                disp_materials.append(material)
                mat_set.add(material)
                displacement_emission_node = tree.nodes['disp_emission']
                mat_output_node = tree.nodes['Material Output']

                tree.links.new(
                    displacement_emission_node.outputs['Emission'],
                    mat_output_node.inputs['Surface'])

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
    #preview_mesh = disp_obj.mt_object_props.linked_object
    #preview_mesh.hide_viewport = False
    disp_obj.hide_viewport = False

    #context.scene.render.bake.use_selected_to_active = True
    #context.scene.render.use_bake_lores_mesh = True
    #context.scene.render.bake.cage_extrusion = 1
    context.scene.render.bake_type = 'DISPLACEMENT'
    context.scene.render.bake_margin = 10

    # temporarily assign a displacement material so we can bake to an image
    '''
    for material in disp_obj.data.materials:
        disp_obj.data.materials.pop(index=0)
    disp_obj.data.materials.append(disp_materials[0])
    '''
    ctx = {
        'selected_objects': [disp_obj],
        'selected_editable_objects': [disp_obj],
        'active_object': disp_obj,
        'object': disp_obj
    }

    # bake
    bpy.ops.object.bake(ctx, type='EMIT')

    # pack image
    disp_image.pack()

    # reset shaders
    for material in disp_materials:
        tree = material.node_tree
        surface_shader_node = tree.nodes['surface_shader']
        displacement_node = tree.nodes['final_disp']
        mat_output_node = tree.nodes['Material Output']
        tree.links.new(surface_shader_node.outputs['BSDF'], mat_output_node.inputs['Surface'])
        tree.links.new(displacement_node.outputs['Displacement'], mat_output_node.inputs['Displacement'])

    '''

    '''
    # store which material is assigned to which vertex group
    for group in disp_obj.vertex_groups:
        disp_obj['preview_materials'][group.name] = get_vert_group_material(group, disp_obj)
        # print(get_vert_group_material(group, disp_obj).name)

    # assign secondary material to entire mesh
    sec_mat_index = get_material_index(disp_obj, bpy.data.materials[prefs.secondary_material])

    for poly in disp_obj.data.polygons:
        poly.material_index = sec_mat_index

    return disp_image, disp_obj
