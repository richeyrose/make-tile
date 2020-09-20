import bpy
from ..tile_creation.create_tile import convert_to_displacement_core, lock_all_transforms
from .. lib.utils.selection import (
    deselect_all,
    select,
    activate)
from .. lib.utils.collections import (
    create_collection,
    add_object_to_collection,
    get_collection)


class MT_OT_Convert_To_MT_Obj(bpy.types.Operator):
    '''Convert a mesh into a MakeTile object'''
    bl_idname = "object.convert_to_make_tile"
    bl_label = "Convert to MakeTile object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.type in {'MESH'}

    def execute(self, context):
        obj = context.object

        scene = context.scene
        scene_props = scene.mt_scene_props
        scene_collection = scene.collection

        # creates a converted objects collection if one doesn't already exist
        converted_obj_collection = create_collection('Converted Objects', scene_collection)

        # create a new collection named after our object as a sub collection
        # of the converted objects collection
        new_collection = bpy.data.collections.new(obj.name)
        converted_obj_collection.children.link(new_collection)
        collection = get_collection(context.view_layer.layer_collection, new_collection.name)
        bpy.context.view_layer.active_layer_collection = collection

        # UV Project
        ctx = {
            'selected_objects': [obj],
            'selected_editable_objects':[obj],
            'object': obj,
            'active_object': obj
        }
        bpy.ops.uv.smart_project(ctx, island_margin=0.01)

        # move object to new collection
        add_object_to_collection(obj, new_collection.name)

        # set some object props
        obj_props = obj.mt_object_props
        obj_props.is_mt_object = True
        obj_props.is_converted = True

        # Yeah it might not be a tile technically. Deal with it :P
        obj_props.tile_name = new_collection.name

        # set some props on the "Tile" collection
        tile_props = new_collection.mt_tile_props
        tile_props.tile_name = new_collection.name
        tile_props.is_mt_collection = True
        tile_props.displacement_strength = scene_props.displacement_strength
        tile_props.tile_resolution = scene_props.tile_resolution
        tile_props.subdivisions = scene_props.subdivisions

        # We assume we want to add texture to entire object and so create an
        # "All" vertex group if there isn't one already
        if 'All' not in obj.vertex_groups:
            group = obj.vertex_groups.new(name="All")
            verts = []
            for vert in obj.data.vertices:
                verts.append(vert.index)
            group.add(verts, 1.0, 'ADD')

        textured_vertex_groups = ['All']
        lock_all_transforms(obj)
        convert_to_displacement_core(obj, textured_vertex_groups)

        # create an empty that we will parent our object to
        object_empty = bpy.data.objects.new(obj.name + ".empty", None)
        add_object_to_collection(object_empty, new_collection.name)
        object_empty.location = obj.location
        object_empty.rotation_euler = obj.rotation_euler
        object_empty.show_in_front = True

        ctx = {
            'selected_objects': [object_empty, obj],
            'active_object': object_empty,
            'object': object_empty}

        bpy.ops.object.parent_set(ctx, type='OBJECT', keep_transform=True)
        deselect_all()
        activate(object_empty.name)
        select(object_empty.name)

        return {'FINISHED'}
