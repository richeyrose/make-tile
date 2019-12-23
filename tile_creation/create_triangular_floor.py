import os
from math import radians
from .. utils.registration import get_prefs
import bpy
from .. lib.turtle.scripts.openlock_floor_tri_base import draw_openlock_tri_floor_base
from .. lib.turtle.scripts.primitives import draw_tri_prism
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, activate, deselect_all, select_all


def create_triangular_floor(tile_empty):
    """Returns a triangular floor"""
    tile_properties = tile_empty['tile_properties']

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_size'][2] = .2756
        tile_properties['tile_size'][2] = 0.374
        base = create_openlock_base(tile_properties)

    if tile_properties['base_blueprint'] == 'PLAIN':
        base = create_plain_base(tile_properties)

    if tile_properties['base_blueprint'] == 'NONE':
        tile_properties['base_size'] = (0, 0, 0)
        base = bpy.data.objects.new(tile_properties['tile_name'] + '.base', None)
        add_object_to_collection(base, tile_properties['tile_name'])

    base.parent = tile_empty
    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc
    tile_empty['tile_properties'] = tile_properties


def create_openlock_base(tile_properties):
    base, dimensions = draw_openlock_tri_floor_base(
        tile_properties['x_leg'],
        tile_properties['y_leg'],
        tile_properties['base_size'][2],
        tile_properties['angle_1'])
    base.name = tile_properties['tile_name'] + '.base'
    add_object_to_collection(base, tile_properties['tile_name'])
    base['geometry_type'] = 'BASE'

    clip_cutters = create_openlock_base_clip_cutter(base, dimensions, tile_properties)

    for clip_cutter in clip_cutters:
        matrixcopy = clip_cutter.matrix_world.copy()
        clip_cutter.parent = base
        clip_cutter.matrix_world = matrixcopy
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter
    return base


def create_openlock_base_clip_cutter(base, dimensions, tile_properties):
    mode('OBJECT')
    deselect_all()
    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

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

    clip_cutter_2 = clip_cutter_1.copy()
    add_object_to_collection(clip_cutter_2, tile_properties['tile_name'])
    clip_cutter_3 = clip_cutter_1.copy()
    add_object_to_collection(clip_cutter_3, tile_properties['tile_name'])

    # for cutters the number of cutters and start and end location has to take into account
    # the angles of the triangle in order to prevent overlaps between cutters
    # and issues with booleans

    # cutter 1
    if dimensions['A'] >= 90:
        clip_cutter_1.location = (
            dimensions['loc_A'][0] + 0.5,
            dimensions['loc_A'][1] + 0.25,
            dimensions['loc_A'][2])
        if dimensions['C'] >= 90:
            array_mod.fit_length = dimensions['c'] - 1
        else:
            array_mod.fit_length = dimensions['c'] - 1.5

    elif dimensions['A'] < 90:
        clip_cutter_1.location = (
            dimensions['loc_A'][0] + 1,
            dimensions['loc_A'][1] + 0.25,
            dimensions['loc_A'][2])
        if dimensions['C'] >= 90:
            array_mod.fit_length = dimensions['c'] - 1.5
        else:
            array_mod.fit_length = dimensions['c'] - 2

    deselect_all()
    select(clip_cutter_1.name)
    bpy.ops.transform.rotate(
        value=(radians(dimensions['A'] - 90)),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=dimensions['loc_A'])

    deselect_all()

    # cutter 2
    array_mod = clip_cutter_2.modifiers['Array']

    if dimensions['B'] >= 90:
        clip_cutter_2.location = (
            dimensions['loc_B'][0] + 0.25,
            dimensions['loc_B'][1] - 0.5,
            dimensions['loc_B'][2])
        if dimensions['A'] >= 90:
            array_mod.fit_length = dimensions['b'] - 1
        else:
            array_mod.fit_length = dimensions['b'] - 1.5

    elif dimensions['B'] < 90:
        clip_cutter_2.location = (
            dimensions['loc_B'][0] + 0.25,
            dimensions['loc_B'][1] - 1,
            dimensions['loc_B'][2])
        if dimensions['A'] >= 90:
            array_mod.fit_length = dimensions['b'] - 1.5
        else:
            array_mod.fit_length = dimensions['b'] - 2

    clip_cutter_2.rotation_euler = (0, 0, radians(-90))

    # cutter 3
    array_mod = clip_cutter_2.modifiers['Array']

    if dimensions['C'] >= 90:
        clip_cutter_3.location = (
            dimensions['loc_C'][0] + 0.5,
            dimensions['loc_C'][1] + 0.25,
            dimensions['loc_C'][2])
        if dimensions['B'] >= 90:
            array_mod.fit_length = dimensions['a'] - 1
        else:
            array_mod.fit_length = dimensions['a'] - 1.5

    elif dimensions['C'] < 90:
        clip_cutter_3.location = (
            dimensions['loc_C'][0] + 1,
            dimensions['loc_C'][1] + 0.25,
            dimensions['loc_C'][2])
        if dimensions['B'] >= 90:
            array_mod.fit_length = dimensions['a'] - 1.5
        else:
            array_mod.fit_length = dimensions['a'] - 2
    deselect_all()
    select(clip_cutter_3.name)

    bpy.ops.transform.rotate(
        value=(-radians(90 + dimensions['C'])),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=dimensions['loc_C'])

    deselect_all()
    cutters = [clip_cutter_1, clip_cutter_2, clip_cutter_3]
    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)
    
    return cutters


def create_plain_base(tile_properties):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    t.add_turtle()
    t.add_vert()
    t.pd()
    base = draw_tri_prism(
        tile_properties['x_leg'],
        tile_properties['y_leg'],
        tile_properties['angle_1'],
        tile_properties['base_size'][2])
    mode('OBJECT')
    return base
