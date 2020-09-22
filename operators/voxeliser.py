import bpy
from bpy.types import Panel
from .. lib.utils.collections import get_objects_owning_collections


class MT_PT_Voxelise_Panel(Panel):
    bl_order = 9
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.operator('scene.mt_voxelise_objects', text='Voxelise Objects')
        layout.prop(scene_props, 'voxel_size')
        layout.prop(scene_props, 'voxel_adaptivity')
        layout.prop(scene_props, 'voxel_merge')


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
        scene_props = context.scene.mt_scene_props
        merge = scene_props.voxel_merge
        selected_objects = context.selected_objects
        meshes = []

        depsgraph = context.evaluated_depsgraph_get()

        for obj in selected_objects:
            if context.object.type == 'MESH':
                meshes.append(obj.data)
                # low level version of apply all modifiers
                object_eval = obj.evaluated_get(depsgraph)
                mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                obj.modifiers.clear()
                obj.data = mesh_from_eval

        ctx = {
            'selected_objects': selected_objects,
            'selected_editable_objects': selected_objects,
            'object': context.active_object,
            'active_object': context.active_object
        }

        if merge is True:
            bpy.ops.object.join(ctx)

        selected_objects = [obj for obj in context.selected_editable_objects if obj.type == 'MESH']
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.data.remesh_voxel_size = scene_props.voxel_size
                obj.data.remesh_voxel_adaptivity = scene_props.voxel_adaptivity
                ctx = {
                    'selected_editable_objects': selected_objects,
                    'selected_objects': selected_objects,
                    'object': obj,
                    'active_object': obj
                }

                bpy.ops.object.voxel_remesh(ctx)
                obj.mt_object_props.geometry_type = 'VOXELISED'

        for mesh in bpy.data.meshes:
            if mesh is not None:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)

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
        scene_props = context.scene.mt_scene_props
        merge = scene_props.voxel_merge
        selected_objects = context.selected_objects

        sel_obs_names = []

        for obj in selected_objects:
            sel_obs_names.append(obj.name)

        for name in sel_obs_names:
            obj_collections = get_objects_owning_collections(name)

            for collection in obj_collections:
                tile_collections.add(collection)

        for collection in tile_collections:
            ctx = {
                'selected_editable_objects': collection.all_objects,
                'selected_objects': collection.all_objects
            }

            for obj in collection.objects:
                if obj.visible_get() is True:
                    sel_obs_names.append(obj.name)

            for name in sel_obs_names:
                if name in collection.objects:
                    obj = bpy.data.objects[name]
                    ctx['object'] = obj
                    ctx['active_object'] = obj
                    bpy.ops.object.convert(ctx, target='MESH', keep_original=False)

            for obj in collection.all_objects:
                if obj.name not in sel_obs_names:
                    bpy.data.objects.remove(obj, do_unlink=True)

            ctx = {
                'selected_editable_objects': collection.all_objects,
                'selected_objects': collection.all_objects,
                'active_object': collection.all_objects[0],
                'object': collection.all_objects[0]
            }

            if merge is True:
                '''
                for obj in collection.all_objects:
                    obj.select_set(True)
                '''
                obj = collection.all_objects[0]

                bpy.ops.object.join(ctx)

                ctx = {
                    'selected_objects': collection.all_objects,
                    'selected_editable_objects': collection.all_objects,
                    'active_object': collection.all_objects[0],
                    'object': collection.all_objects[0]}

                obj = collection.all_objects[0]
                obj.data.remesh_voxel_size = scene_props.voxel_size
                obj.data.remesh_voxel_adaptivity = scene_props.voxel_adaptivity

                bpy.ops.object.voxel_remesh(ctx)

                obj.mt_object_props.geometry_type = 'VOXELISED'

            else:
                for obj in collection.all_objects:
                    obj.data.remesh_voxel_size = scene_props.voxel_size
                    obj.data.remesh_voxel_adaptivity = scene_props.voxel_adaptivity
                    ctx['active_object'] = obj
                    ctx['object'] = obj
                    bpy.ops.object.voxel_remesh(ctx)
                    obj.mt_object_props.geometry_type = 'VOXELISED'

        return {'FINISHED'}


def voxelise(obj):
    """Voxelise the passed in object

    Args:
        obj (bpy.types.Object): object to be voxelised
    """

    obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_size
    obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity

    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj],
        'selected_editable_objects': [obj]}
    obj.hide_set(False)

    bpy.ops.object.convert(ctx, target='MESH', keep_original=False)
    bpy.ops.object.voxel_remesh(ctx)
    obj.mt_object_props.geometry_type = 'VOXELISED'
