import bpy
from ..tile_creation.create_tile import (
    convert_to_displacement_core,
    lock_all_transforms,
    create_helper_object,
    create_common_tile_props,
    spawn_empty_base)
from .. lib.utils.selection import (
    deselect_all,
    select,
    activate)
from .. lib.utils.collections import (
    create_collection,
    add_object_to_collection,
    activate_collection)


from ..utils.registration import get_prefs


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
        prefs = get_prefs()
        obj = context.object
        scene = context.scene
        scene_props = scene.mt_scene_props

        # creates a converted objects collection if one doesn't already exist
        converted_obj_collection = create_collection('Converted Objects', scene.collection)

        # create helper object for material mapping
        create_helper_object(context)

        # create a new collection named after our object as a sub collection
        # of the converted objects collection
        tile_collection = bpy.data.collections.new(obj.name)
        converted_obj_collection.children.link(tile_collection)
        activate_collection(tile_collection.name)

        # move object to new collection
        add_object_to_collection(obj, tile_collection.name)

        # Create tile properties
        tile_props = tile_collection.mt_tile_props
        create_common_tile_props(scene_props, tile_props, tile_collection)

        # create empty and parent our object to it
        base = spawn_empty_base(tile_props)
        base.location = obj.location
        base.rotation_euler = obj.rotation_euler
        ctx = {
            'selected_objects': [base, obj],
            'active_object': base,
            'object': base}

        bpy.ops.object.parent_set(ctx, type='OBJECT', keep_transform=True)

        # UV Project
        ctx = {
            'selected_objects': [obj],
            'selected_editable_objects': [obj],
            'object': obj,
            'active_object': obj
        }

        bpy.ops.object.editmode_toggle(ctx)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle(ctx)

        # set object props
        obj_props = obj.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_collection.name

        # tagging this as a converted object prevents MakeTile from updating the tile options
        # panel when this object is selected.
        obj_props.is_converted = True
        base.mt_object_props.is_converted = True

        # Remove any existing materials
        obj.data.materials.clear()
        # append secondary material
        obj.data.materials.append(bpy.data.materials[prefs.secondary_material])

        # create an all vertex group and ensuire it is at index 0 as otherwise
        # the return to preview feature doesn't work properly
        group = obj.vertex_groups.new(name="All")
        verts = []
        for vert in obj.data.vertices:
            verts.append(vert.index)
        group.add(verts, 1.0, 'ADD')

        obj.vertex_groups.active_index = group.index
        while group.index > 0:
            bpy.ops.object.vertex_group_move(ctx, direction='UP')

        # check to see if there are already vertex groups on the object.
        # If there are we assume that we want the material to be applied to each
        # vertex group
        if len(obj.vertex_groups) > 1:
            textured_vertex_groups = [group.name for group in obj.vertex_groups if group.name != 'All']
        # otherwise we assume we want to add the material to the entire object
        else:
            textured_vertex_groups = ['All']

        # convert our object to a displacement object
        convert_to_displacement_core(obj, textured_vertex_groups)

        # lock all transforms so we can only move parent
        lock_all_transforms(obj)

        # select and activate parent
        deselect_all()
        activate(base.name)
        select(base.name)

        return {'FINISHED'}
