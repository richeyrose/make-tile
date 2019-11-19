'''contains operator class for baking displacement maps to tiles'''
import bpy
from .. materials.materials import bake_displacement_map, add_blank_material
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
            disp_mod.strength = 8
        else:
            disp_mod.strength = -8

        subsurf_mod = displacement_obj.modifiers[displacement_obj['subsurf_mod_name']]
        subsurf_mod.levels = 8

        preview_obj.hide_viewport = True

        displacement_obj.data.materials.clear()
        add_blank_material(displacement_obj)

        return {'FINISHED'}
