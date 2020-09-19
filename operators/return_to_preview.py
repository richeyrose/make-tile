import bpy
from ..lib.utils.selection import deselect_all
from ..materials.materials import assign_mat_to_vert_group
from ..utils.registration import get_prefs

class MT_OT_Return_To_Preview(bpy.types.Operator):
    """Operator class that hides displacement meshes and resets them with appropriate material and
    makes preview meshes visible again"""
    bl_idname = "scene.mt_return_to_preview"
    bl_label = "Return to preview mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()
        disp_obj = bpy.context.object
        #preview_obj = disp_obj.mt_object_props.linked_object
        #preview_obj.hide_viewport = False
        #select(preview_obj.name)
        #activate(preview_obj.name)
        reset_displacement_modifiers(disp_obj)
        disp_obj.mt_object_props.geometry_type = 'PREVIEW'
        #disp_obj.hide_viewport = True

        return {'FINISHED'}


def reset_displacement_modifiers(obj):
    prefs = get_prefs()
    secondary_material = bpy.data.materials[prefs.secondary_material]
    disp_mod = obj.modifiers[obj['disp_mod_name']]
    disp_mod.strength = 0

    assign_mat_to_vert_group('disp_mod_vert_group', obj, secondary_material)
    obj['preview_materials']['disp_mod_vert_group'] = secondary_material.name

    for key, value in obj['preview_materials'].items():
        if key != 'disp_mod_vert_group':
            assign_mat_to_vert_group(key, obj, value)



    # subsurf_mod = obj.modifiers[obj['subsurf_mod_name']]
    # subsurf_mod.levels = 0
