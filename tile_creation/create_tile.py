import bpy
from .. utils.registration import get_prefs
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.selection import select, deselect_all, activate
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials,
    add_preview_mesh_subsurf)

def create_displacement_core(base, preview_core, tile_props, textured_vertex_groups):
    '''Returns the preview and displacement cores'''
    scene = bpy.context.scene
    preferences = get_prefs()

    #preview_core = create_core(tile_props)

    # For some reason iterating doesn't work here so lock these individually so user
    # can only transform base

    preview_core.lock_location[0] = True
    preview_core.lock_location[1] = True
    preview_core.lock_location[2] = True
    preview_core.lock_rotation[0] = True
    preview_core.lock_rotation[1] = True
    preview_core.lock_rotation[2] = True
    preview_core.lock_scale[0] = True
    preview_core.lock_scale[1] = True
    preview_core.lock_scale[2] = True

    preview_core.parent = base

    preview_core, displacement_core = create_displacement_object(preview_core)

    primary_material = bpy.data.materials[scene.mt_scene_props.mt_tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

    # create a vertex group for the displacement modifier
    mod_vert_group_name = construct_displacement_mod_vert_group(displacement_core, textured_vertex_groups)

    assign_displacement_materials(
        displacement_core,
        [image_size, image_size],
        primary_material,
        secondary_material,
        vert_group=mod_vert_group_name)

    assign_preview_materials(
        preview_core,
        primary_material,
        secondary_material,
        textured_vertex_groups)

    preview_core.mt_object_props.geometry_type = 'PREVIEW'
    displacement_core.mt_object_props.geometry_type = 'DISPLACEMENT'

    return preview_core, displacement_core


def finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot):
    # Assign secondary material to our base if its a mesh
    if base.type == 'MESH':
        prefs = get_prefs()
        base.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # Add subsurf modifier to our cores
    if preview_core is not None:
        add_preview_mesh_subsurf(preview_core)

    # Reset location
    base.location = cursor_orig_loc
    cursor = bpy.context.scene.cursor
    cursor.location = cursor_orig_loc
    cursor.rotation_euler = cursor_orig_rot

    deselect_all()
    select(base.name)
    activate(base.name)


class MT_Tile:
    def __init__(self, tile_props):
        self.tile_props = tile_props
        scene = bpy.context.scene
        cursor = scene.cursor
        cursor_orig_loc = cursor.location.copy()
        cursor_orig_rot = cursor.rotation_euler.copy()

        cursor.location = (0, 0, 0)
        cursor.rotation_euler = (0, 0, 0)

        base_blueprint = tile_props.base_blueprint
        main_part_blueprint = tile_props.main_part_blueprint

        if base_blueprint == 'PLAIN':
            base = self.create_plain_base(tile_props)

        if base_blueprint == 'OPENLOCK':
            base = self.create_openlock_base(tile_props)

        if base_blueprint == 'NONE':
            base = self.create_empty_base(tile_props)

        if main_part_blueprint == 'PLAIN':
            preview_core = self.create_plain_cores(base, tile_props)

        if main_part_blueprint == 'OPENLOCK':
            preview_core = self.create_openlock_cores(base, tile_props)

        if main_part_blueprint == 'NONE':
            preview_core = None

        self.finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

    def create_plain_base(self, tile_props):
        pass

    def create_openlock_base(self, tile_props):
        pass

    def create_empty_base(self, tile_props):
        tile_props.base_size = (0, 0, 0)
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        base.show_in_front = True
        add_object_to_collection(base, tile_props.tile_name)
        return base

    def create_plain_cores(self, base, tile_props):
        pass

    def create_openlock_cores(self, base, tile_props):
        pass

    def create_core(self, tile_props):
        pass

    def create_cores(self, base, tile_props, textured_vertex_groups):
        '''Returns the preview and displacement cores'''
        scene = bpy.context.scene
        preferences = get_prefs()

        preview_core = self.create_core(tile_props)

        # For some reason iterating doesn't work here so lock these individually so user
        # can only transform base

        preview_core.lock_location[0] = True
        preview_core.lock_location[1] = True
        preview_core.lock_location[2] = True
        preview_core.lock_rotation[0] = True
        preview_core.lock_rotation[1] = True
        preview_core.lock_rotation[2] = True
        preview_core.lock_scale[0] = True
        preview_core.lock_scale[1] = True
        preview_core.lock_scale[2] = True

        preview_core.parent = base

        preview_core, displacement_core = create_displacement_object(preview_core)


        primary_material = bpy.data.materials[scene.mt_scene_props.mt_tile_material_1]
        secondary_material = bpy.data.materials[preferences.secondary_material]

        image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

        # create a vertex group for the displacement modifier
        mod_vert_group_name = construct_displacement_mod_vert_group(displacement_core, textured_vertex_groups)

        assign_displacement_materials(
            displacement_core,
            [image_size, image_size],
            primary_material,
            secondary_material,
            vert_group=mod_vert_group_name)

        assign_preview_materials(
            preview_core,
            primary_material,
            secondary_material,
            textured_vertex_groups)

        preview_core.mt_object_props.geometry_type = 'PREVIEW'
        displacement_core.mt_object_props.geometry_type = 'DISPLACEMENT'

        return preview_core, displacement_core

    def finalise_tile(self, base, preview_core, cursor_orig_loc, cursor_orig_rot):
        # Assign secondary material to our base if its a mesh
        if base.type == 'MESH':
            prefs = get_prefs()
            base.data.materials.append(bpy.data.materials[prefs.secondary_material])

        # Add subsurf modifier to our cores
        if preview_core is not None:
            add_preview_mesh_subsurf(preview_core)

        # Reset location
        base.location = cursor_orig_loc
        cursor = bpy.context.scene.cursor
        cursor.location = cursor_orig_loc
        cursor.rotation_euler = cursor_orig_rot

        deselect_all()
        select(base.name)
        activate(base.name)
