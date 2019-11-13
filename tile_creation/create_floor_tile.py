import os
import bpy
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, activate
from .. utils.registration import get_path
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base


def create_rectangular_floor( 
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        bhas_base):

    """"Returns a floor
    Keyword arguments:
    tile_system -- tile system for slabs
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z],
    base_system -- tile system for bases
    bhas_base   -- whether tile has a seperate base or is a simple slab
    """
    if bhas_base:
        floor = create_rectangular_floor_base(
            base_system,
            tile_size,
            tile_name,
            base_size)
        return floor

    floor = create_rectangular_floor_slab(
        tile_name,
        tile_size)
    return floor


def create_rectangular_floor_slab(
        tile_name,
        tile_size):

    '''Returns the slab part of a floor tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
    slab_mesh = bpy.data.meshes.new("slab_mesh")
    slab = bpy.data.objects.new(tile_name + '.slab', slab_mesh)
    add_object_to_collection(slab, tile_name)

    select(slab.name)
    activate(slab.name)

    slab = draw_cuboid(tile_size)

    mode('OBJECT')

    # move slab so centred and set origin to world origin
    slab.location = (-tile_size[0] / 2, -tile_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    return slab


def create_rectangular_floor_base(
        base_system,
        tile_size,
        tile_name,
        base_size):

    if base_system == 'OPENLOCK':
        draw_openlock_rect_floor_base(dimensions=tile_size)

    mode('OBJECT')
    base = bpy.context.object
    return base
