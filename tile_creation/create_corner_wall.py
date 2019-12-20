import bpy
from math import tan, radians
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.vertex_groups import corner_wall_to_vert_groups
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. materials.materials import (
    assign_displacement_materials_2,
    assign_preview_materials_2)


def create_corner_wall(tile_empty):
    """Returns a corner wall tile
    Keyword arguments:
    tile_empty -- EMPTY, empty which the tile is parented to. \
        Stores properties that relate to the entire tile
    """
    tile_properties = tile_empty['tile_properties']
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # then moves base to cursor original location and resets cursor
    # TODO: get rid of hack and parent properly
    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    base = create_plain_base(tile_properties)
    wall = create_plain_wall(tile_properties, base)
    base.parent = tile_empty


def create_plain_wall(tile_properties, base):
    textured_faces = tile_properties['textured_faces']
    
    preview_core = create_plain_wall_core(tile_properties)
    preview_core.name = tile_properties['tile_name'] + '.core.preview'
    preview_core['geometry_type'] = 'PREVIEW'
    add_object_to_collection(preview_core, tile_properties['tile_name'])

    displacement_core = create_plain_wall_core(tile_properties)
    displacement_core.name = tile_properties['tile_name'] + '.core.displacement'
    add_object_to_collection(displacement_core, tile_properties['tile_name']) 
    displacement_core['geometry_type'] = 'DISPLACEMENT'

    preview_core['displacement_obj'] = displacement_core
    displacement_core['preview_obj'] = preview_core

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[tile_properties['tile_materials']['tile_material_1']]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials_2(displacement_core, [image_size, image_size], primary_material, secondary_material, textured_faces)
    assign_preview_materials_2(preview_core, primary_material, secondary_material, textured_faces)

    displacement_core.hide_viewport = True


def create_plain_base(tile_properties):

    x_leg_len = tile_properties['x_leg']
    y_leg_len = tile_properties['y_leg']
    base_height = tile_properties['base_size'][2]
    angle = tile_properties['angle_1']
    base_thickness = tile_properties['base_size'][1]

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()

    base_triangles = calculate_corner_wall_triangles(x_leg_len, y_leg_len, base_thickness, angle)

    base_outline = draw_corner_outline(base_triangles, angle, base_thickness)
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    t.pu()
    t.deselect_all()
    t.home()
    bpy.ops.object.editmode_toggle()
    base = bpy.context.object

    return base


def calculate_corner_wall_triangles(
        x_leg_len,
        y_leg_len,
        thickness,
        angle):
    # X leg
    # right triangle
    tri_a_angle = angle / 2
    tri_a_adj = x_leg_len
    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    # right triangle
    tri_b_angle = 180 - tri_a_angle - 90
    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))

    # Y leg
    # right triangle
    tri_c_angle = angle / 2
    tri_c_adj = y_leg_len
    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_angle = 180 - tri_c_angle - 90
    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,
        'b_adj': tri_b_adj,
        'c_adj': tri_c_adj,
        'd_adj': tri_d_adj}

    return triangles


def move_cursor_to_wall_start(triangles, angle, thickness, base_height):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
    orig_rot = turtle.rotation_euler.copy()
    t.pu()
    t.up(d=base_height, m=True)
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    t.lt(d=90)
    t.fd(d=thickness)
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    turtle.rotation_euler = orig_rot


def draw_corner_outline(triangles, angle, thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    orig_loc = turtle.location.copy()
    orig_rot = turtle.rotation_euler.copy()

    # We save the location of each vertex as it is drawn to use for making vert groups later
    vert_loc = {
        'a': orig_loc
    }
    t.pd()
    # draw X leg
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    vert_loc['b'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=thickness)
    vert_loc['c'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    vert_loc['d'] = turtle.location.copy()

    # home
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    t.deselect_all()
    t.select_at_cursor()
    t.pd()  # vert loc same as a

    # draw Y leg
    t.fd(d=triangles['c_adj'])
    vert_loc['e'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=thickness)
    vert_loc['f'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=triangles['d_adj'])  # vert loc same as d

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    return vert_loc


def create_plain_wall_core(tile_properties):

    base_thickness = tile_properties['base_size'][1]
    wall_thickness = tile_properties['tile_size'][1]
    base_height = tile_properties['base_size'][2]
    wall_height = tile_properties['tile_size'][2]
    x_leg_len = tile_properties['x_leg']
    y_leg_len = tile_properties['y_leg']
    angle = tile_properties['angle_1']

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    thickness_diff = base_thickness - wall_thickness

    # first work out where we're going to start drawing our wall
    # from, taking into account the difference in thickness
    # between the base and wall and how long our legs will be
    core_triangles_1 = calculate_corner_wall_triangles(
        x_leg_len,
        y_leg_len,
        thickness_diff / 2,
        angle)

    move_cursor_to_wall_start(
        core_triangles_1,
        angle,
        thickness_diff / 2,
        base_height)

    core_x_leg = core_triangles_1['b_adj']
    core_y_leg = core_triangles_1['d_adj']

    # work out dimensions of core
    core_triangles_2 = calculate_corner_wall_triangles(
        core_x_leg,
        core_y_leg,
        wall_thickness,
        angle)

    # store the vertex locations for turning
    # into vert groups as we draw outline
    vert_locs = draw_corner_outline(
        core_triangles_2,
        angle,
        wall_thickness)

    # fill face and extrude wall
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=wall_height - base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.uv.smart_project()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    t.pu()
    t.deselect_all()
    t.home()

    # create vert groups
    corner_wall_to_vert_groups(bpy.context.object, vert_locs)

    mode('OBJECT')
    core = bpy.context.object

    return core
