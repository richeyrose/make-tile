import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Add_Object_To_Tile(bpy.types.Operator):
    """adds the selected object to the active object's tile collection
    and changes the selected object's type to ADDITIONAL """
    bl_idname = "object.add_to_tile"
    bl_label = "Add to Tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True

    def execute(self, context):
        selected_objects = context.selected_objects
        active_obj = context.active_object
        active_obj_props = active_obj.mt_object_props
        tile_collection = bpy.data.collections[active_obj_props.tile_name]

        for obj in selected_objects:
            if obj is not active_obj:
                obj_props = obj.mt_object_props
                obj_props.geometry_type = 'ADDITIONAL'
                obj_collections = get_objects_owning_collections(obj.name)

                for collection in obj_collections:
                    collection.objects.unlink(obj)

                tile_collection.objects.link(obj)

        return {'FINISHED'}
