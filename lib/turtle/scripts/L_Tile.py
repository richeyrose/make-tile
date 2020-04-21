from math import tan, radians
import bpy
from ... utils.selection import select_by_loc
from ... utils.utils import mode


def draw_corner_floor(triangles, angle, thickness, floor_height, base_height, inc_vert_locs=True):
    '''Returns a corner floor and optionally locations of bottom verts'''
    vert_locs, floor = draw_corner_2D(triangles, angle, thickness, return_object=True)

    mode('EDIT')
    t = bpy.ops.turtle
    t.select_all()
    t.pd()
    t.up(d=floor_height - base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()

    t.deselect_all()
    t.set_position(v=(0, 0, 0))
    t.set_rotation(v=(0, 0, 0))

    mode('OBJECT')

    if inc_vert_locs is False:
        return floor
    else:
        return floor, vert_locs


def draw_corner_wall(triangles, angle, thickness, wall_height, base_height, inc_vert_locs=True):
    '''Returns a corner wall and optionally locations of bottom verts'''
    vert_locs = draw_corner_2D(triangles, angle, thickness)
    mode('EDIT')
    t = bpy.ops.turtle
    t.select_all()
    t.pd()
    t.up(d=0.001)
    t.up(d=wall_height - base_height - 0.011)
    t.up(d=0.01)
    t.select_all()

    bpy.ops.mesh.normals_make_consistent()

    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=(0, 0, 0))

    mode('OBJECT')
    obj = bpy.context.object

    if inc_vert_locs is False:
        return obj
    else:
        return obj, vert_locs


def draw_corner_3D(triangles, angle, thickness, height, inc_vert_locs=False):
    '''Returns a 3D corner piece and optionally locations of bottom verts'''
    vert_loc = draw_corner_2D(triangles, angle, thickness)

    mode('EDIT')
    t = bpy.ops.turtle
    t.select_all()
    t.pd()
    t.up(d=height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=(0, 0, 0))

    mode('OBJECT')
    obj = bpy.context.object

    if inc_vert_locs is False:
        return obj
    else:
        return obj, vert_loc


def draw_corner_wall_core(triangles, angle, thickness, height, native_subdivisions):
    mode('OBJECT')
    obj = bpy.context.object
    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]
    }
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()

    verts = bpy.context.object.data.vertices

    vert_locs = {}
    leg_1_outer_vert_locs = []
    leg_1_end_vert_locs = []
    leg_1_inner_vert_locs = []

    # draw leg_1 #
    # outer
    t.pd()
    t.rt(d=angle)
    subdiv_dist = (triangles['a_adj'] - 0.001) / native_subdivisions[0]
    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=subdiv_dist)
        i += 1
    t.fd(d=0.001)
    for v in verts:
        leg_1_outer_vert_locs.append(v.co.copy())
    vert_locs['Leg 1 Outer'] = leg_1_outer_vert_locs

    # end #
    t.pu()
    t.deselect_all()
    t.lt(d=90)
    leg_1_end_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    t.fd(d=thickness)
    t.pd()
    t.add_vert()
    leg_1_end_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    vert_locs['Leg 1 End'] = leg_1_end_vert_locs

    # inner #
    subdiv_dist = (triangles['b_adj'] - 0.001) / native_subdivisions[0]
    t.lt(d=90)
    t.fd(d=0.001)
    start_index = verts.values()[-1].index
    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=subdiv_dist)
        i += 1

    i = start_index + 1
    while i <= verts.values()[-1].index:
        leg_1_inner_vert_locs.append(verts[i].co.copy())
        i += 1
    t.deselect_all()    
    leg_1_inner_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    vert_locs['Leg 1 Inner'] = leg_1_inner_vert_locs

    # home #
    t.pu()
    t.deselect_all()
    t.home()
    t.select_at_cursor(buffer=0.0001)

    t.pd()

    # draw leg 2 #
    leg_2_outer_vert_locs = []
    leg_2_end_vert_locs = []
    leg_2_inner_vert_locs = []

    # outer #
    leg_2_outer_vert_locs.append(verts[0].co.copy())

    subdiv_dist = (triangles['c_adj'] - 0.001) / native_subdivisions[1]
    start_index = verts.values()[-1].index
    i = 0
    while i < native_subdivisions[1]:
        t.fd(d=subdiv_dist)
        i += 1
    t.fd(d=0.001)

    i = start_index + 1
    while i <= verts.values()[-1].index:
        leg_2_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    t.deselect_all()
    vert_locs['Leg 2 Outer'] = leg_2_outer_vert_locs

    # end #
    t.pu()
    t.rt(d=90)
    leg_2_end_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    t.fd(d=thickness)
    t.pd()
    t.add_vert()
    leg_2_end_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    vert_locs['Leg 2 End'] = leg_2_end_vert_locs

    # inner #
    t.rt(d=90)

    subdiv_dist = (triangles['d_adj'] - 0.001) / native_subdivisions[1]
    t.fd(d=0.001)
    start_index = verts.values()[-1].index
    i = 0
    while i < native_subdivisions[1]:
        t.fd(d=subdiv_dist)
        i += 1

    i = start_index + 1
    while i <= verts.values()[-1].index:
        leg_2_inner_vert_locs.append(verts[i].co.copy())
        i += 1
    t.deselect_all()
    leg_2_inner_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    vert_locs['Leg 2 Inner'] = leg_2_inner_vert_locs
    t.select_all()
    t.merge()
    t.pu()
    t.home()
    bpy.ops.mesh.bridge_edge_loops(ctx, interpolation='LINEAR', number_cuts=native_subdivisions[2])
    t.select_all()
    bpy.ops.mesh.inset(ctx, thickness=0.001, depth=0)
    t.select_all()
    bpy.ops.mesh.remove_doubles(ctx)

    # Z #
    subdiv_dist = (height - 0.002) / native_subdivisions[3]
    t.pd()
    t.up(d=0.001)

    i = 0
    while i < native_subdivisions[3]:
        t.up(d=subdiv_dist)
        i += 1
    t.up(d=0.001)

    mode('OBJECT')
    return bpy.context.object, vert_locs


def draw_corner_2D(triangles, angle, thickness, return_object=False):
    '''Draws a 2D corner mesh in which is an "L" shape
    and returns a dict containing the location of the verts for making vert
    groups later and optionally the object.'''
    mode('OBJECT')

    turtle = bpy.context.scene.cursor
    orig_loc = turtle.location.copy()
    orig_rot = turtle.rotation_euler.copy()
    t = bpy.ops.turtle
    t.add_turtle()

    # We save the location of each vertex as it is drawn
    # to use for making vert groups & positioning cutters
    vert_loc = {
        'origin': orig_loc
    }
    t.pd()
    # draw X leg
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'] - 0.001)
    vert_loc['x_outer_1'] = turtle.location.copy()
    t.fd(d=0.001)
    
    vert_loc['x_outer_2'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=0.001)
    vert_loc['end_1_1'] = turtle.location.copy()
    t.fd(d=thickness - 0.002)
    vert_loc['end_1_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['end_1_3'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=0.001)
    vert_loc['x_inner_1'] = turtle.location.copy()
    t.fd(d=triangles['b_adj'] - 0.001)
    vert_loc['x_inner_2'] = turtle.location.copy()
    # home
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    t.deselect_all()
    t.select_at_cursor(buffer=0.0001)
    t.pd()  # vert loc same as a

    # draw Y leg
    t.fd(d=triangles['c_adj'] - 0.001)
    vert_loc['y_outer_1'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['y_outer_2'] = turtle.location.copy()
    t.rt(d=90)

    t.fd(d=0.001)
    vert_loc['end_2_1'] = turtle.location.copy()

    t.fd(d=thickness - 0.002)
    vert_loc['end_2_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['end_2_3'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['y_inner_1'] = turtle.location.copy()
    t.fd(d=triangles['d_adj'] - 0.001)  # vert loc same as x_inner_2

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()

    select_by_loc(
        lbound=vert_loc['origin'],
        ubound=vert_loc['origin'],
        buffer=0.0001)

    select_by_loc(
        lbound=vert_loc['x_inner_2'],
        ubound=vert_loc['x_inner_2'],
        buffer=0.0001,
        additive=True)

    bpy.ops.mesh.vert_connect_path()

    select_by_loc(
        lbound=vert_loc['y_inner_1'],
        ubound=vert_loc['y_inner_1'],
        buffer=0.0001
    )
    select_by_loc(
        lbound=vert_loc['y_outer_1'],
        ubound=vert_loc['y_outer_1'],
        buffer=0.0001,
        additive=True
    )

    bpy.ops.mesh.vert_connect_path()

    select_by_loc(
        lbound=vert_loc['x_inner_1'],
        ubound=vert_loc['x_inner_1'],
        buffer=0.0001)

    select_by_loc(
        lbound=vert_loc['x_outer_1'],
        ubound=vert_loc['x_outer_1'],
        buffer=0.0001,
        additive=True)

    bpy.ops.mesh.vert_connect_path()

    mode('OBJECT')

    if return_object is False:
        return vert_loc
    else:
        return vert_loc, bpy.context.object


def calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle):
    # X leg
    # right triangle
    tri_a_angle = angle / 2
    tri_a_adj = leg_1_len
    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    # right triangle
    tri_b_angle = 180 - tri_a_angle - 90
    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))

    # Y leg
    # right triangle
    tri_c_angle = angle / 2
    tri_c_adj = leg_2_len
    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_angle = 180 - tri_c_angle - 90
    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,  # leg 1 outer leg length
        'b_adj': tri_b_adj,  # leg 1 inner leg length
        'c_adj': tri_c_adj,  # leg 2 outer leg length
        'd_adj': tri_d_adj}  # leg 2 inner leg length

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
