import os
import bpy
from .. lib.turtle.scripts.curved_floor import draw_neg_curved_slab, draw_pos_curved_slab
from .. lib.utils.vertex_groups import curved_floor_to_vert_groups
from .. utils.registration import get_prefs
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.selection import select, activate, deselect_all, select_all, select_by_loc
from .. lib.utils.utils import mode

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

    base = create_plain_base(tile_properties)

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
