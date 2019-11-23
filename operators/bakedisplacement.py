'''contains operator class for baking displacement maps to tiles'''
import bpy
from .. materials.materials import add_blank_material
from .. lib.utils.selection import deselect_all, select_all, select, activate


class MT_OT_Bake_Displacement(bpy.types.Operator):
    """Operator class to bake displacement maps"""
    bl_idname = "scene.bake_displacement"
    bl_label = "Bake a displacement map"

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        preview_obj = bpy.context.object
        displacement_obj = preview_obj['displacement_obj']
        preview_material = bpy.data.materials[context.scene.mt_tile_material]
        displacement_obj.hide_viewport = False

        deselect_all()
        select(displacement_obj.name)
        activate(displacement_obj.name)

        disp_image = displacement_obj['disp_image']

        bake_displacement_map(preview_material, disp_image, displacement_obj)

        disp_texture = displacement_obj['disp_texture']
        disp_image = displacement_obj['disp_image']
        disp_texture.image = disp_image
        disp_mod = displacement_obj.modifiers[displacement_obj['disp_mod_name']]
        disp_mod.texture = disp_texture
        disp_mod.mid_level = 0
        if displacement_obj['disp_dir'] == 'pos':
            disp_mod.strength = 0.31
        else:
            disp_mod.strength = -0.31

        subsurf_mod = displacement_obj.modifiers[displacement_obj['subsurf_mod_name']]
        subsurf_mod.levels = 8

        preview_obj.hide_viewport = True

        displacement_obj.data.materials.clear()
        add_blank_material(displacement_obj)

        return {'FINISHED'}


def bake_displacement_map(material, image, obj):
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

    # assign image to image node
    texture_node = tree.nodes['disp_texture_node']
    texture_node.image = image

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
