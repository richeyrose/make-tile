import bpy
from .. tile_creation.create_displacement_mesh import create_displacement_object
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials,
    add_preview_mesh_subsurf)
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.collections import (
    create_collection,
    activate_collection,
    add_object_to_collection)
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group


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
        self.convert_to_make_tile_obj(context, obj)
        return {'FINISHED'}

    def convert_to_make_tile_obj(self, context, obj):
        scene = context.scene
        scene_props = scene.mt_scene_props
        scene_collection = scene.collection

        # creates a converted objects collection if one doesn't already exist
        converted_obj_collection = create_collection('Converted Objects', scene_collection)

        # create a new collection named after our object as a sub collection
        # of the converted objects collection
        obj_collection = create_collection(obj.name, converted_obj_collection)
        activate_collection(obj_collection.name)

        # UV Project
        ctx = {
            'selected_objects': [obj],
            'object': obj,
            'active_object': obj
        }
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        # duplicate object and make local
        new_obj = obj.copy()
        new_obj.data = new_obj.data.copy()

        # hide original object
        obj.hide_viewport = True

        # move new object to new collection
        add_object_to_collection(new_obj, obj_collection.name)

        # set some object props
        new_obj.name = obj_collection.name + '.converted'
        obj_props = new_obj.mt_object_props
        obj_props.is_mt_object = True

        # Yeah it might not be a tile technically. Deal with it :P
        obj_props.tile_name = obj_collection.name

        # set some props on the "Tile" collection
        tile_props = obj_collection.mt_tile_props
        tile_props.tile_name = obj_collection.name
        tile_props.is_mt_collection = True
        tile_props.displacement_strength = scene_props.mt_displacement_strength
        tile_props.tile_resolution = scene_props.mt_tile_resolution
        tile_props.subdivisions = scene_props.mt_subdivisions

        # We assume we want to add texture to entire object and so create an
        # "All" vertex group if there isn't one already
        if 'All' not in new_obj.vertex_groups:
            group = new_obj.vertex_groups.new(name="All")
            verts = []
            for vert in new_obj.data.vertices:
                verts.append(vert.index)
            group.add(verts, 1.0, 'ADD')

        textured_vertex_groups = ['All']

        # Create a displacement object that will be used for adding textures to
        preview_obj, displacement_obj = create_displacement_object(new_obj)

        # create an empty that we will parent our object to
        object_empty = bpy.data.objects.new(new_obj.name + ".empty", None)
        add_object_to_collection(object_empty, obj_collection.name)
        object_empty.location = preview_obj.location
        object_empty.rotation_euler = preview_obj.rotation_euler
        object_empty.show_in_front = True

        ctx = {
            'selected_objects': [object_empty, preview_obj, displacement_obj],
            'active_object': object_empty,
            'object': object_empty
        }

        bpy.ops.object.parent_set(ctx, type='OBJECT', keep_transform=True)

        # Get prefs from scene
        prefs = get_prefs()

        primary_material = bpy.data.materials[bpy.context.scene.mt_scene_props.mt_tile_material_1]
        secondary_material = bpy.data.materials[prefs.secondary_material]

        image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

        # We only apply the displacement modifier to this vertex group which prevents
        # the displacement appearing where we don;t want it to
        mod_vert_group_name = construct_displacement_mod_vert_group(
            displacement_obj,
            textured_vertex_groups)

        # Assign our materials
        assign_displacement_materials(
            displacement_obj,
            [image_size, image_size],
            primary_material,
            secondary_material,
            vert_group=mod_vert_group_name)

        assign_preview_materials(
            preview_obj,
            primary_material,
            secondary_material,
            textured_vertex_groups)

        add_preview_mesh_subsurf(preview_obj)

        displacement_obj.hide_viewport = True
