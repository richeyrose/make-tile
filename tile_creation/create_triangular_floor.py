import bpy
from .. lib.turtle.scripts.openlock_floor_tri_base import draw_openlock_tri_floor_base
from .. lib.turtle.scripts.primitives import draw_tri_prism
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode

def create_triangular_floor(tile_empty):
    """Returns a triangular floor"""
    tile_properties = tile_empty['tile_properties']

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)

    if tile_properties['base_blueprint'] == 'OPENLOCK':
        tile_properties['base_size'][2] = .2756
        tile_properties['tile_size'][2] = 0.374
        base = draw_openlock_base(tile_properties)
        
    if tile_properties['base_blueprint'] == 'PLAIN':
        base = draw_plain_base(tile_properties)

    if tile_properties['base_blueprint'] == 'NONE':
        tile_properties['base_size'] = (0, 0, 0)
        base = bpy.data.objects.new(tile_properties['tile_name'] + '.base', None)
        add_object_to_collection(base, tile_properties['tile_name'])

    base.parent = tile_empty
    tile_empty.location = cursor_orig_loc
    cursor.location = cursor_orig_loc
    tile_empty['tile_properties'] = tile_properties


def draw_openlock_base(tile_properties):
    base = draw_openlock_tri_floor_base(
        tile_properties['x_leg'],
        tile_properties['y_leg'],
        tile_properties['base_size'][2],
        tile_properties['angle_1'])

    return base


def draw_plain_base(tile_properties):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    t.add_turtle()
    t.add_vert()
    t.pd()
    base = draw_tri_prism(
        tile_properties['x_leg'],
        tile_properties['y_leg'],
        tile_properties['angle_1'],
        tile_properties['base_size'][2])
    mode('OBJECT')
    return base
