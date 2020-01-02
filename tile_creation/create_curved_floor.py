import os
import bpy
from math import radians
from .. lib.turtle.scripts.curved_floor import draw_neg_curved_slab, draw_pos_curved_slab, draw_openlock_pos_curved_slab
from .. lib.utils.vertex_groups import curved_floor_to_vert_groups
from .. utils.registration import get_prefs
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.selection import select, activate, deselect_all, select_all, select_by_loc
from .. lib.utils.utils import mode
from .. lib.utils.collections import add_object_to_collection


def create_curved_floor(tile_empty):
    scene = bpy.context.scene

    tile_properties = tile_empty['tile_properties']
    tile_properties['radius'] = scene.mt_base_inner_radius
    tile_properties['segments'] = scene.mt_segments
    tile_properties['angle'] = scene.mt_angle_1
    tile_properties['base_height'] = scene.mt_base_z
    tile_properties['tile_height'] = scene.mt_tile_z
    tile_properties['curve_type'] = scene.mt_curve_type

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_height'] = 0.2756
        tile_properties['tile_height'] = 0.374
        base = create_openlock_base(tile_properties)

    if tile_properties['base_blueprint'] == 'PLAIN':
        base = create_plain_base(tile_properties)

    if tile_properties['base_blueprint'] == 'NONE':
        tile_properties['base_size'] = (0, 0, 0)
        base = bpy.data.objects.new(tile_properties['tile_name'] + '.base', None)
        add_object_to_collection(base, tile_properties['tile_name'])

    preview_slab, displacement_slab = create_slabs(tile_properties, base)

    displacement_slab.hide_viewport = True
    base.parent = tile_empty
    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc
    tile_empty['tile_properties'] = tile_properties


def create_plain_base(tile_properties):
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_properties['radius']
    segments = tile_properties['segments']
    angle = tile_properties['angle']
    height = tile_properties['base_height']
    curve_type = tile_properties['curve_type']

    if curve_type == 'POS':
        draw_pos_curved_slab(radius, segments, angle, height)
    else:
        draw_neg_curved_slab(radius, segments, angle, height)
    base = bpy.context.object
    base['geometry_type'] = 'BASE'
    cursor.location = cursor_orig_loc
    select(base.name)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    deselect_all()
    return base


def create_openlock_base(tile_properties):
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_properties['radius']
    segments = tile_properties['segments']
    angle = tile_properties['angle']
    height = tile_properties['base_height']
    curve_type = tile_properties['curve_type']

    if curve_type == 'POS':
        draw_openlock_pos_curved_slab(radius, segments, angle, height)
        base = bpy.context.object

    base['geometry_type'] = 'BASE'
    cursor.location = cursor_orig_loc
    select(base.name)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    deselect_all()

    cutters = create_openlock_base_clip_cutters(base, tile_properties)

    for clip_cutter in cutters:
        matrixcopy = clip_cutter.matrix_world.copy()
        clip_cutter.parent = base
        clip_cutter.matrix_world = matrixcopy
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter

    return base


def create_openlock_base_clip_cutters(base, tile_properties):

    mode('OBJECT')
    deselect_all

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_properties['radius']
    segments = tile_properties['segments']
    angle = tile_properties['angle']
    height = tile_properties['base_height']
    curve_type = tile_properties['curve_type']

    if radius >= 1:
        preferences = get_prefs()
        booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

        cutters = []
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

        for obj in data_to.objects:
            add_object_to_collection(obj, tile_properties['tile_name'])

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
        add_object_to_collection(clip_cutter_2, tile_properties['tile_name'])

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

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    if tile_properties['curve_type'] == 'POS':
        clip_cutter_3 = data_to.objects[0]
        add_object_to_collection(clip_cutter_3, tile_properties['tile_name'])

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
    

    return cutters


def create_slabs(tile_properties, base):
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_properties['radius']
    segments = tile_properties['segments']
    angle = tile_properties['angle']
    height = tile_properties['tile_height'] - base.dimensions[2]
    curve_type = tile_properties['curve_type']

    cursor.location[2] = cursor.location[2] + base.dimensions[2]

    if curve_type == 'POS':
        draw_pos_curved_slab(radius, segments, angle, height)
    else:
        draw_neg_curved_slab(radius, segments, angle, height)

    preview_slab = bpy.context.object
    preview_slab, displacement_slab = create_displacement_object(preview_slab)

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_properties['tile_materials']['tile_material_1']]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution
    deselect_all()
    curved_floor_to_vert_groups(preview_slab, height, radius)

    assign_displacement_materials(
        displacement_slab,
        [image_size, image_size],
        primary_material,
        secondary_material)
    assign_preview_materials(
        preview_slab,
        primary_material,
        secondary_material,
        ['Top'])

    slabs = [preview_slab, displacement_slab]

    cursor.location = cursor_orig_loc

    for slab in slabs:
        deselect_all()
        select(slab.name)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project()
        slab.parent = base

    return preview_slab, displacement_slab
