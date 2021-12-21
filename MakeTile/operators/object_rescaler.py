import bpy


class MT_OT_Rescale_Object(bpy.types.Operator):
    '''Scales an object down to blender units'''
    bl_idname = "object.mt_rescale_object"
    bl_label = "Rescale Object"
    bl_description = "Scale object down for use with MakeTile's material system"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.type == 'MESH'

    def execute(self, context):
        scene_props = context.scene.mt_scene_props
        base_unit = scene_props.base_unit
        cursor_loc = context.scene.cursor.location

        # save current scale lock state
        locked = []
        for obj in context.selected_objects:
            locked.append((obj, obj.lock_scale[0], obj.lock_scale[1], obj.lock_scale[2]))
            obj.lock_scale[0] = False
            obj.lock_scale[1] = False
            obj.lock_scale[2] = False

        # scale objects
        if base_unit == 'INCHES':
            bpy.ops.transform.resize(value=(0.039701, 0.039701, 0.039701), orient_type='GLOBAL', center_override=cursor_loc)
        if base_unit == 'CM':
            bpy.ops.transform.resize(value=(0.01, 0.01, 0.01), orient_type='GLOBAL', center_override=cursor_loc)

        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # restore original scale lock state
        for ob in locked:
            ob[0].lock_scale[0] = ob[1]
            ob[0].lock_scale[1] = ob[2]
            ob[0].lock_scale[2] = ob[3]

        return {'FINISHED'}
