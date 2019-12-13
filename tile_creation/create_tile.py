""" Contains functions for creating tiles """

import os
import bpy
from mathutils import Vector
from .. lib.utils.selection import deselect_all
from .. lib.utils.utils import mode
from .. lib.utils.collections import create_collection, add_object_to_collection, get_collection, activate_collection
from . create_straight_wall_tile import create_straight_wall
from . create_floor_tile import create_rectangular_floor
from . create_curved_wall_tile import create_curved_wall


def create_tile(
        tile_blueprint,
        tile_system,
        tile_type,
        tile_size,
        base_size,
        base_inner_radius,
        wall_inner_radius,
        degrees_of_arc,
        segments,
        base_system,
        tile_material,
        socket_side):
    """Returns a tile as a collection

    """
    scene_collection = bpy.context.scene.collection

    # Check to see if tile collection exist and create if not
    tiles_collection = create_collection('Tiles', scene_collection)

    # construct first part of tile name based on system and type
    tile_name = tile_system.lower() + "." + tile_type.lower()
    deselect_all()
    if tile_type == 'STRAIGHT_WALL' or 'CURVED_WALL':

        # create walls collection if it doesn't already exist
        walls_collection = create_collection('Walls', tiles_collection)

        # create new collection that operates as our "tile" and activate it
        tile_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Walls'].children.link(tile_collection)
        activate_collection(tile_collection.name)

        # make final tile name
        tile_name = tile_collection.name

        bpy.context.scene.mt_tile_name = tile_name

    if tile_type == 'STRAIGHT_WALL':
        create_straight_wall(
            tile_blueprint,
            tile_system,
            tile_name,
            tile_size,
            base_size,
            base_system,
            tile_material)

    if tile_type == 'CURVED_WALL':
        create_curved_wall(
            tile_blueprint,
            tile_system,
            tile_name,
            tile_size,
            base_size,
            base_system,
            tile_material,
            base_inner_radius,
            wall_inner_radius,
            degrees_of_arc,
            segments,
            socket_side)

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
