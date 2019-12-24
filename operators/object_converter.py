import bpy
from .. tile_creation.create_displacement_mesh import convert_to_make_tile_obj


class MT_OT_Convert_To_MT_Obj(bpy.types.Operator):
    '''Convert a mesh into a MakeTile object'''
    bl_idname = "object.convert_to_make_tile"
    bl_label = "Convert to MakeTile object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        obj = context.object
        convert_to_make_tile_obj(obj)

        return {'FINISHED'}
