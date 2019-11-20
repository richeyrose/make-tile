import os
import math
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, select_all, deselect_all, activate
from .. utils.registration import get_path
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base
from . create_straight_wall_tile import create_straight_wall_base
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups


def create_rectangular_floor(
        tile_units,
        tile_system,
        tile_name,
        tile_size,
        base_system,
        bhas_base,
        tile_material):

    """"Returns a floor
    Keyword arguments:
    tile_system -- tile system for slabs
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z],
    base_system -- tile system for bases
    """

    if base_system == "OPENLOCK":
        tile_units = 'IMPERIAL'
        base_size = Vector((tile_size[0], tile_size[1], 0.27559)) * 25.4
        tile_size = Vector((tile_size[0], tile_size[1], 0.27559)) * 25.4

        base = create_openlock_rectangular_floor_base(
            tile_name,
            base_size)
        floor = create_rectangular_floor_slab(
            tile_name,
            tile_size=(tile_size[0], tile_size[1], 1),
            base_size=base_size)
        base.parent = floor

        axes = ['z_pos']

    else:
        floor = create_rectangular_floor_slab(
            tile_name,
            tile_size,
            base_size)

    axes = ['z_pos']

    return floor


def create_rectangular_floor_slab(
        tile_name,
        tile_size,
        base_size):

    '''Returns the slab part of a floor tile

    Keyword arguments:
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
    slab_mesh = bpy.data.meshes.new("slab_mesh")
    slab = bpy.data.objects.new(tile_name + '.slab', slab_mesh)
    add_object_to_collection(slab, tile_name)

    select(slab.name)
    activate(slab.name)

    slab = draw_cuboid(size=(tile_size[0], tile_size[1], tile_size[2]))

    mode('OBJECT')
    select(slab.name)
    activate(slab.name)

    # assign vertex group to each side of mesh
    cuboid_sides_to_vert_groups(slab)

    # Add subsurf modifier that will be used by displacement textures
    mode('EDIT')
    select_all()
    bpy.ops.transform.edge_crease(value=1)
    mode('OBJECT')
    subdiv = slab.modifiers.new('disp_subsurf', 'SUBSURF')

    # move slab so centred and set origin to world origin
    slab.location = (-tile_size[0] / 2, -tile_size[1] / 2, base_size[2])
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    return slab


def create_openlock_rectangular_floor_base(
        tile_name,
        base_size):

    if base_size[0] <= 25.5 and base_size[0] > 12.6 or base_size[1] <= 25.5 and base_size[1] > 12.6:
        # if base is less than an inch use a wall type base
        base = create_straight_wall_base('OPENLOCK', tile_name, base_size)
        base.name
    elif base_size[0] <= 12.6 or base_size[1] <= 12.6:
        print('Tile too small')
        col = bpy.data.collections[tile_name]
        bpy.data.collections.remove(col)
        return False
    else:
        base = draw_openlock_rect_floor_base(base_size)
        base.name = tile_name + '.base'
        add_object_to_collection(base, tile_name)

        clip_cutters = create_openlock_base_clip_cutter(base, tile_name)

        for clip_cutter in clip_cutters:
            clip_cutter.parent = base
            clip_cutter.display_type = 'BOUNDS'
            clip_cutter.hide_viewport = True
            clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
            clip_cutter_bool.operation = 'DIFFERENCE'
            clip_cutter_bool.object = clip_cutter

    mode('OBJECT')
    return base


def create_openlock_base_clip_cutter(base, tile_name):
    """Makes a cutter for the openlock base clip based
    on the width of the base and positions it correctly

    Keyword arguments:
    base -- base the cutter will be used on
    tile_name -- the tile name
    """

    mode('OBJECT')
    base_size = base.dimensions

    # get original location of base and cursor
    base_location = base.location.copy()

    # Get cutter
    deselect_all()
    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")

    # load base cutters
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    # cutter_start_cap.hide_viewport = True
    # cutter_end_cap.hide_viewport = True
    # get location of bottom front left corner of tile
    front_left = [
        base_location[0] - (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        0]

    # move cutter to starting point
    clip_cutter.location = [
        front_left[0] + (0.5 * 25.4),
        front_left[1] + (0.25 * 25.4),
        front_left[2]]

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base_size[0] - 25.4
    select(clip_cutter.name)
    activate(clip_cutter.name)
    mirror_mod = clip_cutter.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = False
    mirror_mod.use_axis[1] = True
    mirror_mod.mirror_object = base

    clip_cutter2 = clip_cutter.copy()
    add_object_to_collection(clip_cutter2, tile_name)
    clip_cutter2.rotation_euler = (0, 0, math.radians(90))
    front_right = [
        base_location[0] + (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        0]
    clip_cutter2.location = [
        front_right[0] - (0.25 * 25.4),
        front_right[1] + (0.5 * 25.4),
        front_right[2]]

    array_mod2 = clip_cutter2.modifiers['Array']
    array_mod2.fit_type = 'FIT_LENGTH'
    array_mod2.fit_length = base_size[1] - 25.4
    mirror_mod2 = clip_cutter2.modifiers['Mirror']
    mirror_mod2.use_axis[0] = True
    mirror_mod2.use_axis[1] = False

    return [clip_cutter, clip_cutter2]
