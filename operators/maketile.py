"""Contains operator class to make tiles"""
import os
from .. materials.materials import load_materials, get_blend_filenames

import bpy
import bpy.utils.previews

from .. utils.registration import get_prefs

from .. lib.utils.selection import deselect_all
from .. lib.utils.collections import (
    create_collection,
    activate_collection)

from .. tile_creation.create_straight_wall_tile import create_straight_wall
from .. tile_creation.create_rect_floor_tile import create_rectangular_floor
from .. tile_creation.create_curved_wall_tile import create_curved_wall
from .. tile_creation.create_corner_wall import create_corner_wall
from .. tile_creation.create_triangular_floor import create_triangular_floor
from .. tile_creation.create_curved_floor import create_curved_floor

from .. property_groups.property_groups import (
    MT_Tile_Properties,
    MT_Object_Properties,
    MT_Scene_Properties)


class MT_OT_Make_Tile(bpy.types.Operator):
    """Create a Tile"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()

        scene = context.scene
        scene_props = scene.mt_scene_props

        ############################################
        # Set defaults for different tile systems #
        ############################################
        tile_blueprint = scene_props.mt_tile_blueprint
        tile_type = scene_props.mt_tile_type

        if tile_blueprint == 'OPENLOCK':
            scene_props.mt_main_part_blueprint = 'OPENLOCK'
            scene_props.mt_base_blueprint = 'OPENLOCK'

        if tile_blueprint == 'PLAIN':
            scene_props.mt_main_part_blueprint = 'PLAIN'
            scene_props.mt_base_blueprint = 'PLAIN'

        #######################################
        # Create our collection and tile name #
        # 'Tiles' are collections of meshes   #
        # parented to an empty                #
        #######################################

        scene_collection = scene.collection

        # Check to see if tile collection exist and create if not
        tiles_collection = create_collection('Tiles', scene_collection)

        # construct first part of tile name based on system and type
        tile_name = tile_blueprint.lower() + "." + tile_type.lower()
        # deselect_all()

        if tile_type == 'STRAIGHT_WALL' or tile_type == 'CURVED_WALL' or tile_type == 'CORNER_WALL':
            # create walls collection if it doesn't already exist
            create_collection('Walls', tiles_collection)

            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Walls'].children.link(tile_collection)

        elif tile_type == 'RECTANGULAR_FLOOR' or tile_type == 'TRIANGULAR_FLOOR' or tile_type == 'CURVED_FLOOR':
            # create floor collection if one doesn't already exist
            create_collection('Floors', tiles_collection)
            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Floors'].children.link(tile_collection)

        # activate collection so objects are added to it
        activate_collection(tile_collection.name)

        # We store tile properties in the mt_tile_props property group of
        # the collection so we can access them from any object in this
        # collection.


        tile_props = tile_collection.mt_tile_props
        tile_props.tile_name = tile_collection.name
        tile_props.is_mt_collection = True
        tile_props.tile_blueprint = tile_blueprint
        tile_props.tile_type = tile_type
        tile_props.main_part_blueprint = scene_props.mt_main_part_blueprint
        tile_props.base_blueprint = scene_props.mt_base_blueprint
        tile_props.tile_size = (scene_props.mt_tile_x, scene_props.mt_tile_y, scene_props.mt_tile_z)
        tile_props.base_size = (scene_props.mt_base_x, scene_props.mt_base_y, scene_props.mt_base_z)
        tile_props.base_radius = scene_props.mt_base_radius
        tile_props.base_socket_side = scene_props.mt_base_socket_side
        tile_props.wall_radius = scene_props.mt_wall_radius
        tile_props.degrees_of_arc = scene_props.mt_degrees_of_arc
        tile_props.angle = scene_props.mt_angle
        tile_props.segments = scene_props.mt_segments
        tile_props.leg_1_len = scene_props.mt_leg_1_len
        tile_props.leg_2_len = scene_props.mt_leg_2_len
        tile_props.curve_type = scene_props.mt_curve_type
        tile_props.tile_units = scene_props.mt_tile_units
        tile_props.displacement_strength = scene_props.mt_displacement_strength
        tile_props.tile_resolution = scene_props.mt_tile_resolution
        tile_props.subdivisions = scene_props.mt_subdivisions

        ###############
        # Create Tile #
        ###############

        if tile_type == 'STRAIGHT_WALL':
            create_straight_wall(tile_props)

        if tile_type == 'CURVED_WALL':
            create_curved_wall(tile_props)

        if tile_type == 'CORNER_WALL':
            create_corner_wall(tile_props)

        if tile_type == 'RECTANGULAR_FLOOR':
            create_rectangular_floor(tile_props)

        if tile_type == 'TRIANGULAR_FLOOR':
            create_triangular_floor(tile_props)

        if tile_type == 'CURVED_FLOOR':
            create_curved_floor(tile_props)

        return {'FINISHED'}

    @classmethod
    def register(cls):
        '''
        material_enum_collection = bpy.utils.previews.new()
        material_enum_collection.directory = ''
        material_enum_collection.enums = ()
        enum_collections["materials"] = material_enum_collection
        enum_collections["materials"] = load_material_enums
        #bpy.utils.previews.remove(material_enum_collection)'''
        # materials = load_material_enums
        

        # Property group that contains properties relating to a tile on the tile collection
        bpy.types.Collection.mt_tile_props = bpy.props.PointerProperty(
            type=MT_Tile_Properties
        )

        # Property group that contains properties of an object stored on the object
        bpy.types.Object.mt_object_props = bpy.props.PointerProperty(
            type=MT_Object_Properties
        )

        # Property group that contains properties set in UI
        bpy.types.Scene.mt_scene_props = bpy.props.PointerProperty(
            type=MT_Scene_Properties
        )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_scene_props
        del bpy.types.Collection.mt_tile_props
        del bpy.types.Object.mt_object_props
