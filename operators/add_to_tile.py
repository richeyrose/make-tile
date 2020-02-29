import bpy

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
        return obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True

    def execute(self, context):
        objects_to_add = []

        for obj in context.selected_objects:
            if obj != context.active_object:
                objects_to_add.append(obj)
                obj.mt_object_props.geometry_type = 'ADDITIONAL'

        context.active_object.select_set(False)
        collection = bpy.data.collections[context.active_object.mt_object_props.tile_name]

        if len(objects_to_add) > 0:
            ctx = {
                'selected_objects': objects_to_add,
                'active_object': objects_to_add[0],
                'object': objects_to_add[0]
            }

            # Unparent the objects we're going to add to our tile
            bpy.ops.object.parent_clear(ctx, type='CLEAR_KEEP_TRANSFORM')

            # apply modifiers if necessary
            if context.scene.mt_apply_modifiers is True:
                depsgraph = context.evaluated_depsgraph_get()
                for obj in objects_to_add:
                    object_eval = obj.evaluated_get(depsgraph)
                    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                    obj.modifiers.clear()
                    obj.data = mesh_from_eval

            base_object = [obj for obj in collection.all_objects if obj.mt_object_props.geometry_type == 'BASE']

            for obj in objects_to_add:
                obj.parent = base_object[0]

        context.active_object.select_set(True)
        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_apply_modifiers = bpy.props.BoolProperty(
            name="Apply Modifiers",
            description="This will apply all modifiers to the object before \
                adding it to the selected tile",
            default=True)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_apply_modifiers
