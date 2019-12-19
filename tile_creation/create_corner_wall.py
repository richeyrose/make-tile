import bpy
from math import tan, radians
from mathutils import Vector


def create_plain_base(base_triangles, base_height, angle, base_thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
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


def calculate_corner_wall_triangles(x_leg_len=2, y_leg_len=3, thickness=0.5, angle=90):
    # X leg
    tri_a_adj = x_leg_len
    tri_a_angle = angle / 2
    tri_b_angle = 180 - tri_a_angle - 90

    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))
    tri_b_hyp = 180 - tri_b_opp - tri_b_adj

    # distance between inner and outer corners of wall
    inner_outer_dist = 180 - tri_a_adj - tri_b_hyp

    # Y leg
    tri_c_adj = y_leg_len

    tri_c_angle = angle / 2
    tri_d_angle = 180 - tri_c_angle - 90

    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,
        'a_opp': tri_a_opp,
        'b_opp': tri_b_opp,
        'b_adj': tri_b_adj,
        'b_hyp': tri_b_hyp,
        'c_adj': tri_c_adj,
        'c_opp': tri_c_opp,
        'd_adj': tri_d_adj,
        'd_opp': tri_d_opp,
        'a_angle': tri_a_angle,
        'b_angle': tri_b_angle,
        'c_angle': tri_c_angle,
        'd_angle': tri_d_angle,
        'inner_outer': inner_outer_dist}
    return triangles


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
        core_triangles,
        base_height,
        wall_height,
        wall_thickness,
        angle):

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
    t.pu()
    t.rt(d=angle / 2)
    t.fd(d=-core_triangles['inner_outer'] / 4)
    t.lt(d=angle / 2)
    core_triangles['a_adj'] = core_triangles['a_adj'] + (core_triangles['inner_outer'] / 4)
    core_triangles['b_adj'] = core_triangles['b_adj'] + (core_triangles['inner_outer'] / 4)
    core_triangles['c_adj'] = core_triangles['c_adj'] + (core_triangles['inner_outer'] / 4)
    core_triangles['d_adj'] = core_triangles['d_adj'] + (core_triangles['inner_outer'] / 4)
    draw_wall_corner_outline(core_triangles, angle, wall_thickness)
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=wall_height - base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.up(d=base_height, m=True)
    t.pu()
    t.deselect_all()
    t.home()
    bpy.ops.object.editmode_toggle()


def create_plain_corner_wall(
        x_leg_len=2,
        y_leg_len=3,
        wall_thickness=0.4,
        wall_height=2,
        angle=90,
        base_thickness=0.5,
        base_height=0.5):

    base_triangles = calculate_corner_wall_triangles(x_leg_len, y_leg_len, base_thickness, angle)
    create_plain_base(base_triangles, base_height, angle, base_thickness)
    core_triangles = calculate_corner_wall_triangles(x_leg_len, y_leg_len, wall_thickness, angle)
    create_plain_wall_core(core_triangles, base_height, wall_height, wall_thickness, angle)
