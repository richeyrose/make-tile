import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Add_Object_To_Tile(bpy.types.Operator):
    """Adds the selected object to the active object's tile collection,
    changes the selected object's type to ADDITIONAL and optionally parents selected
    to active and applies all modifiers"""

    bl_idname = "object.add_to_tile"
    bl_label = "Add to Tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT'

    def execute(self, context):
        sel_obs_names = []

        for obj in context.selected_objects:
            sel_obs_names.append(obj.name)
            obj.select_set(False)

        selected_objects = []

        for obj in bpy.data.objects:
            if obj.name in sel_obs_names:
                selected_objects.append(obj)

        active_obj = context.active_object
        active_obj_props = active_obj.mt_object_props
        active_collection = bpy.data.collections[active_obj_props.tile_name]
        depsgraph = context.evaluated_depsgraph_get()

        for obj in selected_objects:
            if obj is not active_obj:
                obj_props = obj.mt_object_props
                obj_props.geometry_type = 'ADDITIONAL'
                obj_collections = get_objects_owning_collections(obj.name)

                if context.scene.mt_parent_to_new_tile is True:
                    ctx = {
                        'selected_objects': selected_objects,
                        'active_object': active_obj,
                        'object': active_obj
                    }
                    obj.select_set(True)
                    active_obj.select_set(True)

                    bpy.ops.object.parent_set(
                        ctx,
                        type='OBJECT',
                        xmirror=False,
                        keep_transform=True)

                    active_obj.select_set(False)

                if context.scene.mt_apply_modifiers is True:
                    object_eval = obj.evaluated_get(depsgraph)
                    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                    obj.data = mesh_from_eval
                    obj.modifiers.clear()

                obj.select_set(False)

                for collection in obj_collections:
                    collection.objects.unlink(obj)
                active_collection.objects.link(obj)

                obj.mt_object_props.tile_name = active_obj_props.tile_name

        active_obj.select_set(True)

        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_parent_to_new_tile = bpy.props.BoolProperty(
            name="Parent to new tile",
            description="This will allow you to move the object with the parent tile",
            default=True)

        bpy.types.Scene.mt_apply_modifiers = bpy.props.BoolProperty(
            name="Apply Modifiers",
            description="This will apply all modifiers to the object before \
                adding it to the selected tile",
            default=True)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_parent_to_new_tile
        del bpy.types.Scene.mt_apply_modifiers
