import bpy


class MT_OT_Rescale_Object(bpy.types.Operator):
    '''Scales an object down to blender units'''
    bl_idname = "object.mt_rescale_object"
    bl_label = "Rescale Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.type == 'MESH'

    def execute(self, context):
        scene_props = context.scene.mt_scene_props
        base_unit = scene_props.mt_base_unit

        for obj in context.selected_editable_objects:
            if base_unit == 'INCHES':
                obj.scale = obj.scale * 0.039701
            if base_unit == 'CM':
                obj.scale = obj.scale * 0.01

        bpy.ops.object.transform_apply()

        return {'FINISHED'}
