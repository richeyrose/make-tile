""" Contains functions for creating tiles """

import os
import bpy
from .. utils.ut import deselect_all, mode
from .. utils.collections import create_collection, add_object_to_collection
from . create_wall_tile import make_straight_wall
from . create_floor_tile import make_floor

def make_tile(
        tile_units,
        tile_system,
        tile_type,
        bhas_base,
        tile_size,
        base_size,
        base_system):
    """Returns a tile as a collection

        Keyword arguments:
        tile_system -- which tile system the tile will use. ENUM
        tile_type -- e.g. 'WALL', 'FLOOR', 'DOORWAY', 'ROOF'
        tile_size -- [x, y, z]
        base_size -- if tile has a base [x, y, z]
    """
    mode('OBJECT')

    deselect_all()

    scene_collection = bpy.context.scene.collection

    #Check to see if tile, cutters, props and greebles
    # collections exist and create if not
    tiles_collection = create_collection('Tiles', scene_collection)
    walls_collection = create_collection('Walls', tiles_collection)
    floors_collection = create_collection('Floors', tiles_collection)
    props_collection = create_collection('Props', scene_collection)
    greebles_collection = create_collection('Greebles', scene_collection)

    if tile_units == 'IMPERIAL':
        #Switch unit display to inches
        bpy.context.scene.unit_settings.system = 'IMPERIAL'
        bpy.context.scene.unit_settings.length_unit = 'INCHES'
        bpy.context.scene.unit_settings.scale_length = 0.01

    if tile_units == 'METRIC':
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.length_unit = 'METERS'
        bpy.context.scene.unit_settings.scale_length = 1

    # construct first part of tile name based on system and type
    tile_name = tile_system.lower() + "." + tile_type.lower()     

    if tile_type == 'WALL':
        #create new collection that operates as our "tile"
        new_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Walls'].children.link(new_collection)
        tile_name = new_collection.name

        make_straight_wall(
            tile_system,
            tile_name,
            tile_size,
            base_size,
            base_system,
            bhas_base)
        return new_collection

    if tile_type == 'FLOOR':
        #create new collection that operates as our "tile"
        new_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Floors'].children.link(new_collection)
        tile_name = new_collection.name
        
        make_floor(
            tile_system, 
            tile_name, 
            tile_size,
            base_size,
            base_system,
            bhas_base)
        
        return new_collection

    return {'CANCELLED'}
