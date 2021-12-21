import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Delete_Tiles(bpy.types.Operator):
    """Delete the selected Tiles - Warning!!!
    This will delete both the selected object and any collections that object belongs to"""
    bl_idname = "scene.delete_tiles"
    bl_label = "Delete Tiles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj is not None
                and obj.mode == 'OBJECT'
                and obj.mt_object_props.is_mt_object is True)

    def execute(self, context):
        objects = bpy.data.objects
        collections = bpy.data.collections
        selected_objects = context.selected_objects
        tile_collections = []

        for obj in selected_objects:
            obj_collections = get_objects_owning_collections(obj.name)
            for collection in obj_collections:
                tile_collections.append(collection.name)

        for collection in tile_collections:
            if collection in bpy.data.collections:
                for obj in bpy.data.collections[collection].objects:
                    objects.remove(objects[obj.name], do_unlink=True)

                collections.remove(bpy.data.collections[collection], do_unlink=True)
                
        # clean up orphan meshes
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        return {'FINISHED'}
