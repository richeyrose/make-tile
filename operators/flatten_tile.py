import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Flatten_Tile(bpy.types.Operator):
    """Applies all modifiers to the selected objects and 
    any other objects in the same collection then deletes any
    meshes in the objects' owning collection(s) that are not visible"""

    bl_idname = "object.flatten_tiles"
    bl_label = "Flatten_Tiles"
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

        ctx = {
            'selected_objects': selected_objects
        }

        for obj in selected_objects:
            ctx['object'] = obj
            ctx['active_object'] = obj
            bpy.ops.object.convert(ctx, target='MESH', keep_original=False)

            obj_collections = get_objects_owning_collections(obj.name)

            for collection in obj_collections:
                tile_collections.append(collection.name)

        for collection in tile_collections:
            for obj in collections[collection].objects:
                ctx = {
                    'selected_objects': collections[collection].objects
                }
                if obj.hide_viewport is False and obj.hide_get() is False:
                    ctx['object'] = obj
                    ctx['active_object'] = obj
                    obj.select_set(True)
                    bpy.ops.object.convert(ctx, target='MESH', keep_original=False)
                else:
                    ctx['object'] = obj
                    ctx['active_object'] = obj
                    objects.remove(objects[obj.name], do_unlink=True)

        return {'FINISHED'}
