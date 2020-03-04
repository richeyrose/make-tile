import bpy
from .. lib.utils.collections import get_objects_owning_collections


class MT_OT_Object_Voxeliser(bpy.types.Operator):
    """Applies all modifiers to the selected objects and, optionally merges them
    and then voxelises objects"""
    bl_idname = "scene.mt_voxelise_objects"
    bl_label = "Voxelise Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT'

    def execute(self, context):
        merge = context.scene.mt_merge
        selected_objects = context.selected_objects

        depsgraph = context.evaluated_depsgraph_get()

        for obj in selected_objects:
            if context.object.type == 'MESH':
                object_eval = obj.evaluated_get(depsgraph)
                mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                obj.modifiers.clear()
                obj.data = mesh_from_eval

        ctx = {
            'selected_objects': selected_objects,
            'object': context.active_object,
            'active_object': context.active_object
        }

        if merge is True:
            bpy.ops.object.join(ctx)

        for obj in selected_objects:
            obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
            obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity

            ctx['active_object'] = obj
            ctx['object'] = obj

            bpy.ops.object.voxel_remesh(ctx)
            obj.mt_object_props.geometry_type = 'VOXELISED'

        return {'FINISHED'}


class MT_OT_Tile_Voxeliser(bpy.types.Operator):
    """Applies all modifiers to the selected objects and then deletes any
    meshes in the objects' owning collection(s) that are not visible, optionally
    merges them then Voxelises remaining objects."""

    bl_idname = "scene.mt_voxelise_tile"
    bl_label = "Voxelise tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT'

    def execute(self, context):
        tile_collections = set()
        merge = context.scene.mt_merge
        selected_objects = context.selected_objects

        sel_obs_names = []

        for obj in selected_objects:
            sel_obs_names.append(obj.name)

        for name in sel_obs_names:
            obj_collections = get_objects_owning_collections(name)

            for collection in obj_collections:
                tile_collections.add(collection)

        for obj in selected_objects:
            obj.select_set(False)

        for collection in tile_collections:
            ctx = {
                'selected_objects': collection.all_objects
            }

            for obj in collection.objects:
                if obj.visible_get() is True:
                    sel_obs_names.append(obj.name)
                    obj.select_set(True)

            for name in sel_obs_names:
                if name in collection.objects:
                    obj = bpy.data.objects[name]
                    ctx['object'] = obj
                    ctx['active_object'] = obj
                    obj.select_set(True)
                    bpy.ops.object.convert(ctx, target='MESH', keep_original=False)
                    obj.select_set(False)

            for obj in collection.all_objects:
                if obj.name not in sel_obs_names:
                    bpy.data.objects.remove(obj, do_unlink=True)

            ctx = {
                'selected_objects': collection.all_objects,
                'active_object': collection.all_objects[0],
                'object': collection.all_objects[0]
            }

            if merge is True:
                for obj in collection.all_objects:
                    obj.select_set(True)

                obj = collection.all_objects[0]

                bpy.ops.object.join(ctx)

                ctx = {
                    'selected_objects': collection.all_objects,
                    'active_object': collection.all_objects[0],
                    'object': collection.all_objects[0]
                }

                obj = collection.all_objects[0]
                obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
                obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity

                obj.select_set(True)
                bpy.ops.object.voxel_remesh(ctx)
                obj.select_set(False)

                obj.mt_object_props.geometry_type = 'VOXELISED'

            else:
                for obj in collection.all_objects:
                    obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
                    obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity
                    ctx['active_object'] = obj
                    ctx['object'] = obj
                    obj.select_set(True)
                    bpy.ops.object.voxel_remesh(ctx)
                    obj.select_set(False)
                    obj.mt_object_props.geometry_type = 'VOXELISED'

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

        bpy.types.Scene.mt_merge = bpy.props.BoolProperty(
            name="Merge",
            description="Merge tile? Creates a single mesh.",
            default=True
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_merge
        del bpy.types.Scene.mt_voxel_adaptivity
        del bpy.types.Scene.mt_voxel_quality


def voxelise(obj):
    """Voxelises the passed in object
    by default
    Keyword Arguments:
    obj -- bpy.types.Mesh
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
