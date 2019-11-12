import os
import bpy
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, activate
from .. utils.registration import get_path
from .. lib.turtle.scripts.primitives import make_cuboid
from .. lib.turtle.scripts.openlock_floor_base import draw_floor


def make_floor(
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
        '''
        slab = make_floor_slab(
            tile_system,
            tile_name,
            tile_size,
            base_size)
        '''
        base = make_floor_base(
            base_system,
            tile_size,
            tile_name,
            (101.6, 101.6, 7))
        '''
        base.parent = slab
        return slab

    slab = make_floor_slab(
        tile_system,
        tile_name,
        tile_size,
        base_size)
        '''
    return {'FINISHED'}


def make_floor_slab(
        tile_system,
        tile_name,
        tile_size,
        base_size):

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

    slab = make_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    mode('OBJECT')

    # move slab so centred, move up so on top of base and set origin to world origin
    slab.location = (-tile_size[0] / 2, -tile_size[1] / 2, base_size[2])
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    return slab


def make_floor_base(
        base_system,
        tile_size,
        tile_name,
        base_size):

    if base_system == 'OPENLOCK':
        draw_floor(dimensions=base_size)
    '''
    # make base
    base_mesh = bpy.data.meshes.new("base_mesh")
    base = bpy.data.objects.new(tile_name + '.base', base_mesh)
    add_object_to_collection(base, tile_name)
    select(base.name)
    activate(base.name)

    base = make_cuboid(base_size)
    mode('OBJECT')

    # move base so centred and set origin to world origin
    base.location = (- base_size[0] / 2, - base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    '''
    mode('OBJECT')
    base = bpy.context.object
    return base
