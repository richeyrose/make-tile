import os
import bpy
from math import radians
from .. lib.turtle.scripts.curved_floor import draw_neg_curved_slab, draw_pos_curved_slab, draw_openlock_pos_curved_base
from .. lib.turtle.scripts.L_tile import calculate_corner_wall_triangles, move_cursor_to_wall_start, draw_corner_3D
from .. lib.utils.vertex_groups import (
    curved_floor_to_vert_groups,
    construct_displacement_mod_vert_group)
from .. utils.registration import get_prefs
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.selection import select, deselect_all
from .. lib.utils.utils import mode
from .. lib.utils.collections import add_object_to_collection

from . generic import finalise_tile


# TODO: Fix dimensioning disappearing when no base
def create_curved_floor(tile_props):
    scene = bpy.context.scene
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    # Get base and main part blueprints
    base_blueprint = tile_props.base_blueprint
    main_part_blueprint = tile_props.main_part_blueprint

    tile_meshes = []

    if base_blueprint == 'OPENLOCK':
        base = create_openlock_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'PLAIN':
        base = create_plain_base(tile_props)
        tile_meshes.append(base)

    if base_blueprint == 'NONE':
        tile_props['base_size'] = (0, 0, 0)
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        add_object_to_collection(base, tile_props.tile_name)

    if main_part_blueprint == 'OPENLOCK':
        tile_props.tile_size[2] = 0.3
        preview_core, displacement_core = create_cores(tile_props, base)
        tile_meshes.extend([preview_core, displacement_core])
        displacement_core.hide_viewport = True

    if main_part_blueprint == 'PLAIN':
        preview_core, displacement_core = create_cores(tile_props, base)
        tile_meshes.extend([preview_core, displacement_core])
        displacement_core.hide_viewport = True

    if main_part_blueprint == 'NONE':
        tile_props.tile_size = tile_props.base_size
        preview_core = None

    finalise_tile(base,
                  preview_core,
                  cursor_orig_loc)


def create_plain_base(tile_props):
    radius = tile_props.base_radius
    segments = tile_props.segments
    angle = tile_props.angle
    height = tile_props.base_size[2]
    curve_type = tile_props.curve_type

    if curve_type == 'POS':
        base = draw_pos_curved_slab(radius, segments, angle, height)
    else:
        base = draw_neg_curved_slab(radius, segments, angle, height)

    ctx = {
        'selected_objects': [base],
        'active_object': base
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'

    return base


def create_openlock_base(tile_props):
    tile_props.base_size[2] = 0.2756

    length = tile_props.base_radius
    segments = tile_props.segments
    angle = tile_props.angle
    height = tile_props.base_size[2]
    curve_type = tile_props.curve_type

    if curve_type == 'POS':
        base = draw_openlock_pos_curved_base(length, segments, angle, height)
        base.mt_object_props.geometry_type = 'BASE'
        ctx = {
            'selected_objects': [base],
            'active_object': base
        }
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    else:
        draw_neg_curved_slab(length, segments, angle, height)
        base = bpy.context.object
        base.mt_object_props.geometry_type = 'BASE'
        ctx = {
            'selected_objects': [base],
            'active_object': base
        }
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        if length >= 3:
            slot_cutter = create_openlock_neg_curve_base_cutters(tile_props)
            slot_cutter.parent = base
            slot_cutter.display_type = 'BOUNDS'
            slot_cutter.hide_viewport = True
            cutter_bool = base.modifiers.new('Slot Cutter', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = slot_cutter

    cutters = create_openlock_base_clip_cutters(tile_props)

    for clip_cutter in cutters:
        matrixcopy = clip_cutter.matrix_world.copy()
        clip_cutter.parent = base
        clip_cutter.matrix_world = matrixcopy
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'

    return base


def create_openlock_neg_curve_base_cutters(tile_props):
    length = tile_props.base_radius / 2
    angle = tile_props.angle
    face_dist = 0.233
    slot_width = 0.197
    slot_height = 0.25
    end_dist = 0.236  # distance of slot from base end

    cutter_triangles_1 = calculate_corner_wall_triangles(
        length,
        length,
        face_dist,
        angle)

    # reuse method we use to work out where to start our corner wall
    move_cursor_to_wall_start(
        cutter_triangles_1,
        angle,
        face_dist,
        -0.01)

    cutter_x_leg = cutter_triangles_1['b_adj'] - end_dist
    cutter_y_leg = cutter_triangles_1['d_adj'] - end_dist

    # work out dimensions of cutter
    cutter_triangles_2 = calculate_corner_wall_triangles(
        cutter_x_leg,
        cutter_y_leg,
        slot_width,
        angle
    )

    cutter = draw_corner_3D(
        cutter_triangles_2,
        angle,
        slot_width,
        slot_height
    )

    cutter.name = tile_props.tile_name + '.base.cutter'

    props = cutter.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'CUTTER'
    return cutter


def create_openlock_base_clip_cutters(tile_props):

    mode('OBJECT')

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_props.base_radius
    angle = tile_props.angle
    curve_type = tile_props.curve_type
    cutters = []
    if curve_type == 'NEG':
        radius = radius / 2

    if radius >= 1:
        preferences = get_prefs()
        booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)

        clip_cutter_1 = data_to.objects[0]
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        cutter_start_cap.hide_viewport = True
        cutter_end_cap.hide_viewport = True

        array_mod = clip_cutter_1.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'

        if angle >= 90:
            clip_cutter_1.location = (
                cursor_orig_loc[0] + 0.5,
                cursor_orig_loc[1] + 0.25,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1
        else:
            clip_cutter_1.location = (
                cursor_orig_loc[0] + 1,
                cursor_orig_loc[1] + 0.25,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1.5

        deselect_all()
        select(clip_cutter_1.name)

        bpy.ops.transform.rotate(
            value=(radians(angle - 90)),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=cursor_orig_loc)

        cutters.append(clip_cutter_1)
        # cutter 2
        clip_cutter_2 = clip_cutter_1.copy()
        add_object_to_collection(clip_cutter_2, tile_props.tile_name)

        array_mod = clip_cutter_2.modifiers['Array']

        if angle >= 90:
            clip_cutter_2.location = (
                cursor_orig_loc[0] + 0.25,
                cursor_orig_loc[1] + radius - 0.5,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1
        else:
            clip_cutter_2.location = (
                cursor_orig_loc[0] + 0.25,
                cursor_orig_loc[1] + radius - 0.5,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1.5

        clip_cutter_2.rotation_euler = (0, 0, radians(-90))
        cutters.append(clip_cutter_2)

        deselect_all()

    if tile_props.curve_type == 'POS':
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip_single']
        clip_cutter_3 = data_to.objects[0]
        add_object_to_collection(clip_cutter_3, tile_props.tile_name)

        deselect_all()
        select(clip_cutter_3.name)

        clip_cutter_3.rotation_euler = (0, 0, radians(180))
        clip_cutter_3.location[1] = cursor_orig_loc[1] + radius - 0.25
        bpy.ops.transform.rotate(
            value=(radians(angle / 2)),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=cursor_orig_loc)

        cutters.append(clip_cutter_3)

    for cutter in cutters:
        props = cutter.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name
        props.geometry_type = 'CUTTER'

    return cutters


def create_core(base, tile_props):
    radius = tile_props.base_radius
    segments = tile_props.segments
    angle = tile_props.angle
    height = tile_props.tile_size[2] - base.dimensions[2]
    curve_type = tile_props.curve_type

    if curve_type == 'POS':
        preview_core = draw_pos_curved_slab(radius, segments, angle, height)
    else:
        preview_core = draw_neg_curved_slab(radius, segments, angle, height)

    curved_floor_to_vert_groups(
        preview_core,
        height,
        radius)

    preview_core.location[2] = preview_core.location[2] + base.dimensions[2]

    preview_core.name = tile_props.tile_name + '.core'
    deselect_all()
    select(preview_core.name)

    ctx = {
        'selected_objects': [preview_core],
        'object': preview_core,
        'active_object': preview_core
    }

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=0.05)
    preview_core.parent = base

    obj_props = preview_core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    return preview_core


def create_cores(tile_props, base):
    preview_core = create_core(base, tile_props)

    preview_core, displacement_core = create_displacement_object(preview_core)

    preferences = get_prefs()

    primary_material = bpy.data.materials[bpy.context.scene.mt_scene_props.mt_tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_scene_props.mt_tile_resolution

    textured_vertex_groups = ['Top']

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
