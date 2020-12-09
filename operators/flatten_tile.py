import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Flatten_Tile(bpy.types.Operator):
    """Applies all modifiers to the selected objects and
    any other objects in the same collection then deletes any
    meshes in the objects' owning collection(s) that are not visible"""

    bl_idname = "object.flatten_tiles"
    bl_label = "Flatten Tiles"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True

    def execute(self, context):
        selected_objects = context.selected_objects
        tile_collections = set()

        # Save selected object's owning collection(s)
        for obj in selected_objects:
            if obj.type == 'MESH':
                obj_collections = get_objects_owning_collections(obj.name)
                for collection in obj_collections:
                    tile_collections.add(collection)

        for collection in tile_collections:
            flatten_tile(context, collection)
        return {'FINISHED'}


def flatten_tile(context, collection):
    ctx = {
        'selected_objects': collection.all_objects,
        'object': collection.all_objects[0],
        'active_object': collection.all_objects[0]
    }

    # save a list of meshes
    meshes = []
    for obj in collection.all_objects:
        meshes.append(obj.data)

    # Unparent the objects in this collection.
    bpy.ops.object.parent_clear(ctx, type='CLEAR_KEEP_TRANSFORM')

    # get all visible mesh objects
    visible_mesh_objects = [obj for obj in collection.all_objects if obj.type == 'MESH' and obj.visible_get() is True]
    
    # apply all modifiers
    depsgraph = context.evaluated_depsgraph_get()

    for obj in visible_mesh_objects:
        object_eval = obj.evaluated_get(depsgraph)
        mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
        obj.modifiers.clear()
        obj.data = mesh_from_eval

    # join all objects
    if len(visible_mesh_objects) > 1:
        ctx = {
            'object': visible_mesh_objects[0],
            'active_object': visible_mesh_objects[0],
            'selected_objects': visible_mesh_objects,
            'selected_editable_objects': visible_mesh_objects
        }
        bpy.ops.object.join(ctx)

    # Rename duplicate object to collection name
    if len(visible_mesh_objects) > 0:
        visible_mesh_objects[0].name = collection.name

    # Delete all other objects in collection
    for obj in collection.all_objects:
        if obj not in visible_mesh_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Delete all unused meshes in collection
    for mesh in meshes:
        if mesh is not None:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

    # Rename duplicate object to collection name
    if len(visible_mesh_objects) > 0:
        obj = visible_mesh_objects[0]
        obj.name = collection.name

        obj.mt_object_props.geometry_type = 'FLATTENED'
        obj.mt_object_props.is_displacement = False

        return obj

    return None