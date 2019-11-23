import bpy


class MT_OT_Return_To_Preview(bpy.types.Operator):
    """Operator class that hides displacement meshes and resets them with appropriate material and
    makes preview meshes visible again"""
    bl_idname = "scene.return_to_preview"
    bl_label = "Return to preview mesh"

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        disp_obj = bpy.context.object
        preview_obj = disp_obj['preview_obj']
        preview_obj.hide_viewport = False

        reset_displacement_modifiers(disp_obj)

        tile_material = disp_obj['primary_material']    
        disp_obj.data.materials.clear()
        disp_obj.data.materials.append(tile_material)
        disp_obj.hide_viewport = True

        return {'FINISHED'}


def reset_displacement_modifiers(obj):
    disp_mod = obj.modifiers[obj['disp_mod_name']]
    disp_mod.strength = 0
    subsurf_mod = obj.modifiers[obj['subsurf_mod_name']]
    subsurf_mod.levels = 0
