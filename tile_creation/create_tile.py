""" Contains functions for creating tiles """

import os
import bpy
from mathutils import Vector
from .. lib.utils.selection import deselect_all
from .. lib.utils.utils import mode
from .. lib.utils.collections import (
    create_collection,
    activate_collection)
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
        base_blueprint,
        tile_materials,
        base_socket_sides,
        textured_faces):
    """Returns a tile as a collection
    'Tiles' are collections of meshes parented to an empty.
    Properties that apply to the entire tile are stored on the empty
    """
    #######################################
    # Create our collection and tile name #
    #######################################

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

    if tile_type == 'RECTANGULAR_FLOOR':
        # create floor collection if one doesn't already exist
        floors_collection = create_collection('Floors', tiles_collection)
        # create new collection that operates as our "tile" and activate it
        tile_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Floors'].children.link(tile_collection)

    # make final tile name
    activate_collection(tile_collection.name)

    tile_name = tile_collection.name

    #####################
    # Create Tile Empty #
    #####################

    tile_empty = bpy.data.objects.new(tile_name + ".empty", None)
    bpy.context.layer_collection.collection.objects.link(tile_empty)

    # create properties
    tile_empty['tile_properties'] = {
        'tile_name': tile_name,
        'tile_blueprint': tile_blueprint,
        'base_blueprint': base_blueprint,
        'tile_type': tile_type,
        'tile_size': tile_size,
        'base_size': base_size,
        'tile_materials': tile_materials,
        'textured_faces': textured_faces,
        'base_inner_radius': base_inner_radius,  # used for curved tiles only
        'wall_inner_radius': wall_inner_radius,  # used for curved walls only
        'degrees_of_arc': degrees_of_arc,  # used for curved tiles only
        'segments': segments,  # used for curved tiles only
        'base_socket_sides': base_socket_sides,  # used for bases that can or should have sockets only on certain sides
    }

    ###############
    # Create Tile #
    ###############

    if tile_type == 'STRAIGHT_WALL':
        create_straight_wall(tile_empty)

    if tile_type == 'CURVED_WALL':
        create_curved_wall(tile_empty)

    if tile_type == 'RECTANGULAR_FLOOR':
        create_rectangular_floor(tile_empty)

    return tile_collection
