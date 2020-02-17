import bpy

class MT_OT_Delete_Tile(bpy.types.Operator):
    """Delete the selected Tile"""
    bl_idname = "scene.delete_tile"
    bl_label = "Delete a tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True:
            return True
        else:
            return False

    def execute(self, context):
        objects = bpy.data.objects
        obj = context.object
        obj_props = obj.mt_object_props
        collections = bpy.data.collections
        tile_collection = collections[obj_props.tile_name]

        for ob in tile_collection.objects:
            objects.remove(objects[ob.name], do_unlink=True)

        collections.remove(tile_collection, do_unlink=True)

        return {'FINISHED'}
