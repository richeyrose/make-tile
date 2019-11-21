""" Contains functions for creating tiles """

import os
import bpy
from mathutils import Vector
from .. lib.utils.selection import deselect_all
from .. lib.utils.utils import mode
from .. lib.utils.collections import create_collection, add_object_to_collection, get_collection, activate_collection
from . create_straight_wall_tile import create_straight_wall
from . create_floor_tile import create_rectangular_floor


def create_tile(
        tile_blueprint,
        tile_system,
        tile_type,
        tile_size,
        base_size,
        base_system,
        tile_material):
    """Returns a tile as a collection

        Keyword arguments:
        tile_system -- which tile system the tile will use. ENUM
        tile_type -- e.g. 'WALL', 'FLOOR', 'DOORWAY', 'ROOF'
        tile_size -- [x, y, z]
        base_size -- if tile has a base [x, y, z]
    """
    scene_collection = bpy.context.scene.collection

    # Check to see if tile collection exist and create if not
    tiles_collection = create_collection('Tiles', scene_collection)

    # construct first part of tile name based on system and type
    tile_name = tile_system.lower() + "." + tile_type.lower()

    if tile_type == 'STRAIGHT_WALL':

        # create walls collection if it doesn't already exist
        walls_collection = create_collection('Walls', tiles_collection)

        # create new collection that operates as our "tile" and activate it
        tile_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Walls'].children.link(tile_collection)
        activate_collection(tile_collection.name)

        # make final tile name
        tile_name = tile_collection.name

        create_straight_wall(
            tile_blueprint,
            tile_system,
            tile_name,
            tile_size,
            base_size,
            base_system,
            tile_material)

    if tile_type == 'RECTANGULAR_FLOOR':

        # create floor collection if one doesn't already exist
        floors_collection = create_collection('Floors', tiles_collection)
        # create new collection that operates as our "tile" and activate it
        tile_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Floors'].children.link(tile_collection)

        activate_collection(tile_collection.name)
        # make final tile name
        tile_name = tile_collection.name

        create_rectangular_floor(
            tile_blueprint,
            tile_system,
            tile_name,
            tile_size,
            base_size,
            base_system,
            tile_material)

    return tile_collection
