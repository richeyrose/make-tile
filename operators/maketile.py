import bpy
from .. lib.utils.selection import deselect_all
from .. lib.utils.collections import (
    create_collection,
    add_object_to_collection)

#TODO Merge this file with create_tile.py
class MT_Tile_Generator:
    """Subclass this to create your tile operator."""

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True

#TODO get rid of renderer switch
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
    if 'Material Helper Empty' not in bpy.data.objects:
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
    tile_props.texture_margin = scene_props.texture_margin
