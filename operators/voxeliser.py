import bpy
from .. lib.utils.selection import select, deselect_all, select_all, activate
from .. lib.utils.collections import add_object_to_collection, create_collection
from . trim_tile import add_bool_modifier
from .. lib.utils.collections import get_objects_owning_collections

class MT_OT_Tile_Voxeliser(bpy.types.Operator):
    """Applies all modifiers to the selected objects and then deletes any
    meshes in the objects' owning collection(s) that are not visible 
    then Voxelises displacement objects."""

    bl_idname = "scene.mt_voxelise_tile"
    bl_label = "Voxelise tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj is not None and obj.mode == 'OBJECT')

    def execute(self, context):
        objects = bpy.data.objects
        collections = bpy.data.collections
        selected_objects = context.selected_objects
        tile_collections = set()

        ctx = {
            'selected_objects': selected_objects
        }

        for obj in selected_objects:
            ctx['object'] = obj
            ctx['active_object'] = obj
            bpy.ops.object.convert(ctx, target='MESH', keep_original=False)

            obj_collections = get_objects_owning_collections(obj.name)

            for collection in obj_collections:
                tile_collections.add(collection.name)

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
                    obj.select_set(False)
                else:
                    ctx['object'] = obj
                    ctx['active_object'] = obj
                    objects.remove(objects[obj.name], do_unlink=True)

            ctx = {
                'selected_objects': collections[collection].objects
            }

            for obj in collections[collection].objects:
                ctx['selected_objects'] = collections[collection].objects
                ctx['object'] = obj
                ctx['active_object'] = obj

                if obj.mt_object_props.geometry_type == 'DISPLACEMENT':
                    ctx['selected_objects'] = [obj]
                    
                    obj.data.remesh_voxel_size = context.scene.mt_voxel_quality
                    obj.data.remesh_voxel_adaptivity = context.scene.mt_voxel_adaptivity
                    bpy.ops.object.voxel_remesh(ctx)


        if context.scene.mt_merge_and_voxelise is True:
            for collection in tile_collections:
                ctx['selected_objects'] = collections[collection].objects
                ctx['object'] = collections[collection].objects[0]
                ctx['active_object'] = collections[collection].objects[0]

                for obj in collections[collection].objects:
                    obj.select_set(True)

                bpy.ops.object.join(ctx)

                for obj in collections[collection].objects:
                    obj.select_set(False)

                obj = collections[collection].objects[0]
                obj.name = collection

        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_voxel_quality = bpy.props.FloatProperty(
            name="Quality",
            description="Quality of the voxelisation. Smaller = Better",
            soft_min=0.005,
            default=0.0101,
            precision=3,
        )

        bpy.types.Scene.mt_voxel_adaptivity = bpy.props.FloatProperty(
            name="Adaptivity",
            description="Amount by which to simplify mesh",
            default=0.05,
            precision=3,
        )

        bpy.types.Scene.mt_merge_and_voxelise = bpy.props.BoolProperty(
            name="Merge",
            description="Merge tile before voxelising? Creates a single mesh.",
            default=True
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_merge_and_voxelise
        del bpy.types.Scene.mt_voxel_adaptivity
        del bpy.types.Scene.mt_voxel_quality


def voxelise(obj):
    """Voxelises the passed in object and adds a triangulate modifier
    by default
    Keyword Arguments:
    obj -- bpy.types.Object
    """

    obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
    obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity

    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]}
    obj.hide_set(False)
    obj.select_set(True)
    bpy.ops.object.convert(ctx, target='MESH', keep_original=False)
    bpy.ops.object.voxel_remesh(ctx)
    obj.mt_object_props.geometry_type = 'VOXELISED'

    return obj
