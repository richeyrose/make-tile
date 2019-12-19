import bpy
from math import tan, radians
from mathutils import Vector


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

    base = create_plain_base(2, 3, 0.5, 60, 0.5)
    core = create_plain_wall_core(0.5, 0.25, 0.5, 2, 2, 3, 60)


def create_plain_corner_wall(
        x_leg_len=2,
        y_leg_len=3,
        wall_thickness=0.4,
        wall_height=2,
        angle=90,
        base_thickness=0.5,
        base_height=0.5):

    create_plain_base(
        x_leg_len,
        y_leg_len,
        base_height,
        angle,
        base_thickness)

    create_plain_wall_core(
        base_thickness,
        wall_thickness,
        base_height,
        wall_height,
        x_leg_len,
        y_leg_len,
        angle)


def create_plain_base(
        x_leg_len,
        y_leg_len,
        base_height,
        angle,
        base_thickness):

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()

    base_triangles = calculate_corner_wall_triangles(x_leg_len, y_leg_len, base_thickness, angle)

    base_outline = draw_wall_corner_outline(base_triangles, angle, base_thickness)
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.deselect_all()
    t.home()
    bpy.ops.object.editmode_toggle()


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


def move_cursor_to_wall_start(triangles, angle, thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
    orig_rot = turtle.rotation_euler.copy()
    t.pu()
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    t.lt(d=90)
    t.fd(d=thickness)
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    turtle.rotation_euler = orig_rot


def draw_wall_corner_outline(triangles, angle, thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    orig_loc = turtle.location.copy()
    orig_rot = turtle.rotation_euler.copy()
    t.pd()

    # draw X leg
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    t.lt(d=90)
    t.fd(d=thickness)
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])

    # home
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    t.deselect_all()
    t.select_at_cursor()
    t.pd()

    # draw Y leg
    t.fd(d=triangles['c_adj'])
    t.rt(d=90)
    t.fd(d=thickness)
    t.rt(d=90)
    t.fd(d=triangles['d_adj'])

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot


def create_plain_wall_core(
        base_thickness,
        wall_thickness,
        base_height,
        wall_height,
        x_leg_len,
        y_leg_len,
        angle):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    thickness_diff = base_thickness - wall_thickness

    core_triangles_1 = calculate_corner_wall_triangles(x_leg_len, y_leg_len, thickness_diff / 2, angle)
    move_cursor_to_wall_start(core_triangles_1, angle, thickness_diff / 2)

    core_x_leg = core_triangles_1['b_adj']
    core_y_leg = core_triangles_1['d_adj']

    core_triangles_2 = calculate_corner_wall_triangles(core_x_leg, core_y_leg, wall_thickness, angle)
    draw_wall_corner_outline(core_triangles_2, angle, wall_thickness)

    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=base_height, m=True)
    t.up(d=wall_height - base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.deselect_all()
    t.home()
    bpy.ops.object.editmode_toggle()
