import os
import bpy


class MT_OT_Copy_Material(bpy.types.Operator):
    """Copies a material"""
    bl_idname = "material.mt_copy"
    bl_label = "Copy Material"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is not None:
            mat = obj.active_material
            return mat is not None
        return False

    def execute(self, context):
        obj = context.object
        new_material = obj.active_material.copy()
        
        obj.data.materials.append(new_material)

        return {'FINISHED'}