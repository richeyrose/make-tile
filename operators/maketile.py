"""Operator class to make tiles"""
import bpy
from bpy.types import Operator
from .. lib.utils.selection import deselect_all
from .. lib.utils.collections import (
    create_collection,
    add_object_to_collection)

'''
from .. tile_creation.L_Tiles import MT_L_Wall, MT_L_Floor
from .. tile_creation.Straight_Tiles import MT_Straight_Wall_Tile, MT_Straight_Floor_Tile
from .. tile_creation.Curved_Tiles import MT_Curved_Wall_Tile, MT_Curved_Floor_Tile
from .. tile_creation.Rectangular_Tiles import MT_Rectangular_Floor_Tile
from .. tile_creation.Triangular_Tiles import MT_Triangular_Floor_Tile
from .. tile_creation.Semi_Circ_Tiles import MT_Semi_Circ_Floor_Tile
from .. tile_creation.U_Tiles import MT_U_Wall_Tile
from .. tile_creation.Connecting_Column_Tiles import MT_Connecting_Column_Tile
'''

def initialise_tile_creator(context):
    deselect_all()
    scene = context.scene
    scene_props = scene.mt_scene_props

    # Switch renderer to Eevee. This is a hack to compensate
    # for an issue where the tile generators sometimes
    # produce different results depending on what
    # renderer we are using. Hopefully when the turtle
    # is rewritten to work on a bmesh this will no longer
    # be an issue

    original_renderer = scene.render.engine
    if original_renderer != 'BLENDER_EEVEE':
        scene.render.engine = 'BLENDER_EEVEE'

    # Set defaults for different tile systems
    tile_blueprint = scene_props.tile_blueprint
    tile_type = scene_props.tile_type

    if tile_blueprint == 'OPENLOCK':
        scene_props.main_part_blueprint = 'OPENLOCK'
        scene_props.base_blueprint = 'OPENLOCK'

    if tile_blueprint == 'PLAIN':
        scene_props.main_part_blueprint = 'PLAIN'
        scene_props.base_blueprint = 'PLAIN'

    # Root collection to which we add all tiles
    tiles_collection = create_collection('Tiles', scene.collection)

    # Helper object collection
    helper_collection = create_collection('MT Helpers', scene.collection)

    # Used as a reference object for material projection
    material_helper = bpy.data.objects.new('Material Helper Empty', None)
    material_helper.hide_viewport = True
    add_object_to_collection(material_helper, helper_collection.name)

    tile_name = tile_blueprint.lower() + "." + tile_type.lower()

    # We create tile at origin and then move it to original location
    # this stops us from having to update the view layer every time
    # we parent an object
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor_orig_rot = cursor.rotation_euler.copy()
    cursor.location = (0, 0, 0)
    cursor.rotation_euler = (0, 0, 0)

    return original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot


class MT_Tile_Generator:
    """Subclass this to create your tile operator."""

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True
    '''
    def execute(self, context):
        print("Execute")

        initialise_tile_creator(self, context)
        if tile_type in (
                'STRAIGHT_WALL',
                'CURVED_WALL',
                'CORNER_WALL',
                'U_WALL'):
            # create walls collection if it doesn't already exist
            create_collection('Walls', tiles_collection)

            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Walls'].children.link(tile_collection)

        elif tile_type in (
                'RECTANGULAR_FLOOR',
                'TRIANGULAR_FLOOR',
                'CURVED_FLOOR',
                'CORNER_FLOOR',
                'STRAIGHT_FLOOR',
                'SEMI_CIRC_FLOOR'):

            # create floor collection if one doesn't already exist
            create_collection('Floors', tiles_collection)
            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Floors'].children.link(tile_collection)

        elif tile_type in (
                'CONNECTING_COLUMN'):
            create_collection('Columns', tiles_collection)
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Columns'].children.link(tile_collection)

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
        tile_props.main_part_blueprint = scene_props.main_part_blueprint
        tile_props.base_blueprint = scene_props.base_blueprint
        tile_props.UV_island_margin = scene_props.UV_island_margin

        tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
        tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)
        tile_props.base_radius = scene_props.base_radius
        tile_props.base_socket_side = scene_props.base_socket_side
        tile_props.wall_radius = scene_props.wall_radius
        tile_props.degrees_of_arc = scene_props.degrees_of_arc
        tile_props.angle = scene_props.angle

        tile_props.leg_1_len = scene_props.leg_1_len
        tile_props.leg_2_len = scene_props.leg_2_len
        tile_props.curve_type = scene_props.curve_type
        tile_props.openlock_column_type = scene_props.openlock_column_type

        tile_props.tile_units = scene_props.tile_units
        tile_props.displacement_strength = scene_props.displacement_strength
        tile_props.tile_resolution = scene_props.tile_resolution

        tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
        tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
        tile_props.z_native_subdivisions = scene_props.z_native_subdivisions
        tile_props.opposite_native_subdivisions = scene_props.opposite_native_subdivisions
        tile_props.curve_native_subdivisions = scene_props.curve_native_subdivisions
        tile_props.leg_1_native_subdivisions = scene_props.leg_1_native_subdivisions
        tile_props.leg_2_native_subdivisions = scene_props.leg_2_native_subdivisions
        tile_props.width_native_subdivisions = scene_props.width_native_subdivisions
        ###############
        # Create Tile #
        ###############

        if tile_type == 'STRAIGHT_WALL':
            MT_Straight_Wall_Tile(tile_props)

        if tile_type == 'STRAIGHT_FLOOR':
            MT_Straight_Floor_Tile(tile_props)

        if tile_type == 'CURVED_WALL':
            MT_Curved_Wall_Tile(tile_props)

        if tile_type == 'CORNER_WALL':
            MT_L_Wall(tile_props)

        if tile_type == 'CORNER_FLOOR':
            MT_L_Floor(tile_props)

        if tile_type == 'RECTANGULAR_FLOOR':
            MT_Rectangular_Floor_Tile(tile_props)

        if tile_type == 'TRIANGULAR_FLOOR':
            MT_Triangular_Floor_Tile(tile_props)

        if tile_type == 'SEMI_CIRC_FLOOR':
            MT_Semi_Circ_Floor_Tile(tile_props)

        if tile_type == 'CURVED_FLOOR':
            MT_Curved_Floor_Tile(tile_props)

        if tile_type == 'U_WALL':
            MT_U_Wall_Tile(tile_props)

        if tile_type == 'CONNECTING_COLUMN':
            MT_Connecting_Column_Tile(tile_props)

        scene.render.engine = original_renderer
        return {'FINISHED'}
    '''


def create_common_tile_props(scene_props, tile_props, tile_collection):
    """Create properties common to all tiles."""
    tile_props.tile_name = tile_collection.name
    tile_props.is_mt_collection = True
    tile_props.tile_blueprint = scene_props.tile_blueprint
    tile_props.main_part_blueprint = scene_props.main_part_blueprint
    tile_props.base_blueprint = scene_props.base_blueprint
    tile_props.UV_island_margin = scene_props.UV_island_margin
    tile_props.tile_units = scene_props.tile_units
    tile_props.displacement_strength = scene_props.displacement_strength
    tile_props.tile_resolution = scene_props.tile_resolution


class MT_OT_Make_Corner_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Corner Floor Tile."""

    bl_idname = "object.make_corner_floor"
    bl_label = "Corner Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class MT_OT_Make_Triangle_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Triangle Floor Tile."""

    bl_idname = "object.make_triangle_floor"
    bl_label = "Triangle Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class MT_OT_Make_Curved_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Curved Floor Tile"""
    bl_idname = "object.make_curved_floor"
    bl_label = "Curved Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class MT_OT_Make_Semi_Circ_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Semi Circular Floor Tile"""
    bl_idname = "object.make_semi_circ_floor"
    bl_label = "Semi Circular Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}
