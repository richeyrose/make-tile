import os
from random import random
import bpy
from bpy.types import Panel
from .. utils.registration import get_prefs
from .voxeliser import voxelise
from .. lib.utils.collections import get_objects_owning_collections
from . bakedisplacement import (
    set_cycles_to_bake_mode,
    reset_renderer_from_bake,
    bake_displacement_map)
from . return_to_preview import set_to_preview


class MT_PT_Export_Panel(Panel):
    bl_order = 10
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Export_Panel"
    bl_label = "Export"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        prefs = get_prefs()
        layout = self.layout

        layout.operator('scene.mt_export_tile', text='Export Tile')
        layout.prop(prefs, 'default_export_path')
        layout.prop(scene_props, 'export_units')
        layout.prop(scene_props, 'voxelise_on_export')
        layout.prop(scene_props, 'randomise_on_export')

        if scene_props.randomise_on_export is True:
            layout.prop(scene_props, 'num_variants')


class MT_OT_Export_Tile_Variants(bpy.types.Operator):
    bl_idname = "scene.mt_export_multiple_tile_variants"
    bl_label = "Export multiple tile variants"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # set up exporter options
        prefs = get_prefs()
        scene_props = context.scene.mt_scene_props

        #number of variants we will generate
        num_variants = scene_props.num_variants

        # set cycles to bake mode and store original settings
        orig_settings = set_cycles_to_bake_mode()

        # voxelise options
        voxelise_on_export = scene_props.voxelise_on_export

        # ensure export path exists
        export_path = prefs.default_export_path
        if not os.path.exists(export_path):
            os.mkdir(export_path)

        # Controls if we rescale on export
        blend_units = scene_props.export_units
        if blend_units == 'CM':
            unit_multiplier = 10
        elif blend_units == 'INCHES':
            unit_multiplier = 25.4
        else:
            unit_multiplier = 1

        objects = bpy.data.objects
        visible_objects = []

        # get list of tile collections our selected objects are in. We export
        # all visible objects in the collections
        tile_collections = set()
        for obj in context.selected_objects:
            obj_collections = get_objects_owning_collections(obj.name)

            for collection in obj_collections:
                if collection.mt_tile_props.is_mt_collection is True:
                    tile_collections.add(collection)

        for collection in tile_collections:
            visible_objects = []

            for obj in collection.objects:
                if obj.type == 'MESH' and obj.visible_get() is True:
                    visible_objects.append(obj)

            # we will generate variants of preview obs equal to num_variants
            displacement_obs = []
            for obj in visible_objects:
                if obj.mt_object_props.geometry_type == 'PREVIEW':
                    displacement_obs.append(obj)
                if obj.mt_object_props.geometry_type == 'DISPLACEMENT':
                    set_to_preview(obj)
                    displacement_obs.append(obj)

            i = 0
            while i < num_variants:
                # construct a random name for our variant
                file_path = os.path.join(
                    export_path,
                    collection.name + '.' + str(random()) + '.stl')

                # generate a random variant for each displacement object
                for obj in displacement_obs:
                    obj_props = obj.mt_object_props
                    ctx = {
                        'selected_objects': [obj],
                        'selected_editable_objects': [obj],
                        'active_object': obj,
                        'object': obj}

                    for item in obj.material_slots.items():
                        if item[0]:
                            material = bpy.data.materials[item[0]]
                            tree = material.node_tree
                            if 'Seed' in tree.nodes:
                                rand = random()
                                seed_node = tree.nodes['Seed']
                                seed_node.outputs[0].default_value = rand * 1000

                    disp_image, obj = bake_displacement_map(obj)
                    tile_props = collection.mt_tile_props
                    disp_strength = tile_props.displacement_strength
                    disp_texture = obj['disp_texture']
                    disp_texture.image = disp_image
                    disp_mod = obj.modifiers[obj['disp_mod_name']]
                    disp_mod.texture = disp_texture
                    disp_mod.mid_level = 0
                    disp_mod.strength = disp_strength

                    subsurf_mod = obj.modifiers[obj['subsurf_mod_name']]
                    subsurf_mod.levels = scene_props.subdivisions
                    bpy.ops.object.modifier_move_to_index(ctx, modifier=subsurf_mod.name, index=0)
                    obj_props.geometry_type = 'DISPLACEMENT'

                if voxelise_on_export:
                    depsgraph = context.evaluated_depsgraph_get()
                    dupes = []

                    for obj in visible_objects:
                        object_eval = obj.evaluated_get(depsgraph)
                        mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                        dup_obj = bpy.data.objects.new('dupe', mesh_from_eval)
                        dup_obj.location = obj.location
                        dup_obj.rotation_euler = obj.rotation_euler
                        dup_obj.scale = obj.scale
                        dup_obj.parent = obj.parent
                        collection.objects.link(dup_obj)
                        dupes.append(dup_obj)

                    # join dupes together
                    if len(dupes) > 0:
                        ctx = {
                            'object': dupes[0],
                            'active_object': dupes[0],
                            'selected_objects': dupes,
                            'selected_editable_objects': dupes}
                        bpy.ops.object.join(ctx)

                    voxelise(dupes[0])

                    ctx = {
                        'object': dupes[0],
                        'active_object': dupes[0],
                        'selected_objects': [dupes[0]],
                        'selected_editable_objects': [dupes[0]]}

                    # export our object
                    bpy.ops.export_mesh.stl(
                        ctx,
                        filepath=file_path,
                        check_existing=True,
                        filter_glob="*.stl",
                        use_selection=True,
                        global_scale=unit_multiplier,
                        use_mesh_modifiers=True)

                    objects.remove(dupes[0], do_unlink=True)

                    # clean up orphaned meshes
                    for mesh in bpy.data.meshes:
                        if mesh.users == 0:
                            bpy.data.meshes.remove(mesh)
                else:
                    ctx = {
                        'object': visible_objects[0],
                        'active_object': visible_objects[0],
                        'selected_objects': visible_objects,
                        'selected_editable_objects': visible_objects}

                    # export our object
                    bpy.ops.export_mesh.stl(
                        ctx,
                        filepath=file_path,
                        check_existing=True,
                        filter_glob="*.stl",
                        use_selection=True,
                        global_scale=unit_multiplier,
                        use_mesh_modifiers=True)

                for obj in displacement_obs:
                    set_to_preview(obj)
                i += 1

        reset_renderer_from_bake(orig_settings)

        return {'FINISHED'}


class MT_OT_Export_Tile(bpy.types.Operator):
    '''Exports visible contents of current tile as an .stl.'''

    bl_idname = "scene.mt_export_tile"
    bl_label = "Export tile"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True

    def execute(self, context):
        if context.scene.mt_scene_props.randomise_on_export is True:
            bpy.ops.scene.mt_export_multiple_tile_variants()
            return {'PASS_THROUGH'}

        # set up exporter options
        prefs = get_prefs()
        scene_props = context.scene.mt_scene_props

        # voxelise options
        voxelise_on_export = scene_props.voxelise_on_export

        # ensure export path exists
        export_path = prefs.default_export_path
        if not os.path.exists(export_path):
            os.mkdir(export_path)

        # Controls if we rescale on export
        blend_units = scene_props.export_units
        if blend_units == 'CM':
            unit_multiplier = 10
        elif blend_units == 'INCHES':
            unit_multiplier = 25.4
        else:
            unit_multiplier = 1

        objects = bpy.data.objects

        # get list of tile collections our selected objects are in. We export
        # all visible objects in the collections
        tile_collections = set()
        for obj in context.selected_objects:
            obj_collections = get_objects_owning_collections(obj.name)

            for collection in obj_collections:
                tile_collections.add(collection)

        for collection in tile_collections:
            # check if collection is a MakeTile collection
            if collection.mt_tile_props.is_mt_collection is True:
                # create a list of visible objects to export
                visible_objects = []
                for obj in collection.objects:
                    if obj.type == 'MESH' and obj.visible_get() is True:
                        visible_objects.append(obj)

                # construct a random name for our collection
                file_path = os.path.join(
                    export_path,
                    collection.name + '.' + str(random()) + '.stl')

                # if we are voxelising exported mesh we need to merge
                # all objects together and then voxelise them. To do this
                # we create a duplicate of each visible object, apply all modifiers
                # join all meshes together, voxelise the joint mesh, export the joint mesh
                # and then delete it
                if voxelise_on_export:
                    # duplicate
                    depsgraph = context.evaluated_depsgraph_get()
                    dupes = []
                    for obj in visible_objects:
                        object_eval = obj.evaluated_get(depsgraph)
                        mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                        dup_obj = bpy.data.objects.new('dupe', mesh_from_eval)
                        dup_obj.location = obj.location
                        dup_obj.rotation_euler = obj.rotation_euler
                        dup_obj.scale = obj.scale
                        dup_obj.parent = obj.parent
                        collection.objects.link(dup_obj)
                        dupes.append(dup_obj)

                    # join dupes together
                    if len(dupes) > 0:
                        ctx = {
                            'object': dupes[0],
                            'active_object': dupes[0],
                            'selected_objects': dupes,
                            'selected_editable_objects': dupes}
                        bpy.ops.object.join(ctx)

                    # voxelise
                    voxelise(dupes[0])

                    ctx = {
                        'object': dupes[0],
                        'active_object': dupes[0],
                        'selected_objects': [dupes[0]],
                        'selected_editable_objects': [dupes[0]]}

                    # export our object
                    bpy.ops.export_mesh.stl(
                        ctx,
                        filepath=file_path,
                        check_existing=True,
                        filter_glob="*.stl",
                        use_selection=True,
                        global_scale=unit_multiplier,
                        use_mesh_modifiers=True)

                    # delete duplicate objects
                    objects.remove(dupes[0], do_unlink=True)

                    # clean up orphaned meshes
                    for mesh in bpy.data.meshes:
                        if mesh.users == 0:
                            bpy.data.meshes.remove(mesh)
                else:
                    ctx = {
                        'object': visible_objects[0],
                        'active_object': visible_objects[0],
                        'selected_objects': visible_objects,
                        'selected_editable_objects': visible_objects}

                    # export our object
                    bpy.ops.export_mesh.stl(
                        ctx,
                        filepath=file_path,
                        check_existing=True,
                        filter_glob="*.stl",
                        use_selection=True,
                        global_scale=unit_multiplier,
                        use_mesh_modifiers=True)

        return {'FINISHED'}
