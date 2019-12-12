'''contains operator class for baking displacement maps to tiles'''
import bpy
from .. materials.materials import load_secondary_material
from .. lib.utils.selection import deselect_all, select_all, select, activate


class MT_OT_Bake_Displacement(bpy.types.Operator):
    """Operator class to bake displacement maps"""
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
        displacement_obj = preview_obj['displacement_obj']
        preview_material = preview_obj['primary_material']
        resolution = context.scene.mt_tile_resolution
        displacement_obj.hide_viewport = False

        deselect_all()
        select(displacement_obj.name)
        activate(displacement_obj.name)

        bake_displacement_map(preview_material, displacement_obj, resolution)

        disp_texture = displacement_obj['disp_texture']
        disp_image = displacement_obj['disp_image']
        disp_texture.image = disp_image
        disp_mod = displacement_obj.modifiers[displacement_obj['disp_mod_name']]
        disp_mod.texture = disp_texture
        disp_mod.mid_level = 0

        if displacement_obj['disp_dir'] == 'pos' or 'NORMAL':
            disp_mod.strength = displacement_obj['disp_strength']
        elif displacement_obj['disp_dir'] == 'neg':
            disp_mod.strength = -displacement_obj['disp_strength']

        subsurf_mod = displacement_obj.modifiers[displacement_obj['subsurf_mod_name']]

        subsurf_mod.levels = bpy.context.scene.mt_subdivisions

        preview_obj.hide_viewport = True

        displacement_obj.data.materials.clear()
        load_secondary_material()

        return {'FINISHED'}


def bake_displacement_map(material, obj, resolution):
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

    if obj['disp_dir'] == 'neg':
        obj['disp_strength'] = -strength_node.outputs[0].default_value
    else:
        obj['disp_strength'] = strength_node.outputs[0].default_value

    # create image
    image = bpy.data.images.new(obj.name + '.image', width=resolution, height=resolution)
    obj['disp_image'] = image

    # assign image to image node
    texture_node = tree.nodes['disp_texture_node']
    texture_node.image = image

    # project from preview to displacement mesh when baking
    preview_mesh = bpy.data.objects[obj['preview_obj'].name]
    deselect_all()
    select(preview_mesh.name)
    select(obj.name)
    activate(obj.name)
    bpy.context.scene.render.bake.use_selected_to_active = True
    bpy.context.scene.render.bake.cage_extrusion = 1

    # bake
    bpy.ops.object.bake(type='EMIT')

    # pack image
    image.pack()

    # reset shader
    surface_shader_node = tree.nodes['surface_shader']
    tree.links.new(surface_shader_node.outputs['BSDF'], mat_output_node.inputs['Surface'])
    tree.links.new(displacement_node.outputs['Displacement'], mat_output_node.inputs['Displacement'])

    # reset engine
    bpy.context.scene.cycles.samples = orig_samples
    bpy.context.scene.render.tile_x = orig_x
    bpy.context.scene.render.tile_y = orig_y
    bpy.context.scene.cycles.bake_type = orig_bake_type
    bpy.context.scene.render.engine = orig_engine
