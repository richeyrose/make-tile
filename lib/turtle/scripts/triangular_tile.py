import bpy
from . primitives import draw_tri_prism, draw_triangle
from ... utils.utils import mode
from math import sqrt, cos, radians, acos, degrees

def draw_plain_triangular_base(tile_props):
    t = bpy.ops.turtle
    t.add_turtle()
    t.add_vert()
    t.pd()
    base, dimensions = draw_tri_prism(
        tile_props.leg_1_len,
        tile_props.leg_2_len,
        tile_props.angle,
        tile_props.base_size[2])
    t.pu()
    t.home()
    mode('OBJECT')

    return base, dimensions


def draw_triangular_floor_core(tile_props):
    t = bpy.ops.turtle
    t.add_turtle()
    t.add_vert()
    t.pd()
    core, dimensions = draw_tri_prism(
        tile_props.leg_1_len,
        tile_props.leg_2_len,
        tile_props.angle,
        tile_props.tile_size[2] - tile_props.base_size[2])
    t.pu()
    t.home()
    mode('OBJECT')

    return core, dimensions


def draw_openlock_tri_floor_base(x_leg, y_leg, height, angle_1):
    '''Returns an openlock rectangular floor base'''
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    t.add_turtle()

    t.pd()
    t.add_vert()
    start_loc = turtle.location.copy()
    base, dimensions = draw_base(x_leg, y_leg, height, start_loc, angle_1)

    return base, dimensions


def draw_base(b, c, height, start_loc, A):
    outer_w = 0.2362                 # outer ring width
    slot_w = 0.1811                # slot width
    slot_h = 0.2402                # slot height
    support_w = 0.11811              # slot support width
    support_h = 0.05472            # slot support height

    t = bpy.ops.turtle
    # loops are numbered from outer to inner

    # draw loop 1 (outer) and save dimensions
    triangle, dimensions = draw_triangle(b, c, A)

    # fill face
    bpy.ops.mesh.edge_face_add()

    # inset to get loop 2
    bpy.ops.mesh.inset(thickness=outer_w, depth=0, use_select_inset=False)

    # inset to get loop 3 and select inset
    bpy.ops.mesh.inset(thickness=slot_w, depth=0, use_select_inset=True)
    # delete face
    bpy.ops.mesh.delete(type='FACE')

    # save loop vert index manually
    loop_1 = [0, 1, 2]
    loop_2 = [6, 7, 8]
    loop_3 = [3, 4, 5]

    t.deselect_all()

    # switch to Object mode because we can only select verts in obj mode obviously /\0/\
    bpy.ops.object.mode_set(mode='OBJECT')

    # select loop 2
    for i in loop_2:
        vert = bpy.context.object.data.vertices[i]
        vert.select = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=support_w, offset_pct=0, vertex_only=True)

    # save bevel verts
    outer_bev_1 = [9, 11]
    outer_bev_2 = [3, 5]
    outer_bev_3 = [6, 8]

    t.deselect_all()

    bpy.ops.object.mode_set(mode='OBJECT')

    # select loop 3
    for i in loop_3:
        vert = bpy.context.object.data.vertices[i]
        vert.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=support_w, offset_pct=0, vertex_only=True)

    # save bevel verts
    inner_bev_1 = [16, 17]
    inner_bev_2 = [12, 13]
    inner_bev_3 = [14, 15]

    t.deselect_all()

    bevels = [
        inner_bev_1 + outer_bev_1,
        inner_bev_2 + outer_bev_2,
        inner_bev_3 + outer_bev_3]

    bpy.ops.object.mode_set(mode='OBJECT')

    for bevel in bevels:
        for i in bevel:
            vert = bpy.context.object.data.vertices[i]
            vert.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()
        t.deselect_all()
        bpy.ops.object.mode_set(mode='OBJECT')

    # extrude up inner slots
    slots = [
        [6, 11, 14, 17],
        [3, 8, 13, 15],
        [5, 9, 12, 16]]

    for slot in slots:
        for i in slot:
            vert = bpy.context.object.data.vertices[i]
            vert.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        t.pd()
        t.up(d=support_h)

        t.deselect_all()
        bpy.ops.object.mode_set(mode='OBJECT')

    supports = [
        [19, 21, 27, 29],
        [18, 20, 23, 25],
        [22, 24, 26, 28]]

    for support in supports:
        for i in support:
            vert = bpy.context.object.data.vertices[i]
            vert.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()
        t.deselect_all()
        bpy.ops.object.mode_set(mode='OBJECT')

    slot_sides = [
        [18, 19, 22, 23, 26, 27],
        [20, 21, 24, 25, 28, 29]]

    for side in slot_sides:
        for i in side:
            vert = bpy.context.object.data.vertices[i]
            vert.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        t.up(d=slot_h - support_h)
        t.deselect_all()
        bpy.ops.object.mode_set(mode='OBJECT')

    slot_top = [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41]
    for i in slot_top:
        vert = bpy.context.object.data.vertices[i]
        vert.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    t.bridge()
    t.deselect_all()
    bpy.ops.object.mode_set(mode='OBJECT')

    for i in loop_1:
        vert = bpy.context.object.data.vertices[i]
        vert.select = True
    bpy.ops.object.mode_set(mode='EDIT')
    t.up(d=height)
    bpy.ops.mesh.edge_face_add()

    t.select_all()
    bpy.ops.mesh.normals_make_consistent()

    t.pu()
    t.home()

    bpy.ops.object.mode_set(mode='OBJECT')

    return bpy.context.object, dimensions

def draw_tri_floor_core(b, c, A, height, native_subdivisions=(15, 2)):
    '''draws a triangle given the length of two sides (b, c) and the angle between them (A).
    native_subdivisions contains subdivs for edges and z axis'''
    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    mode('OBJECT')

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()

    t.pd()
    t.add_vert()

    loc_A = turtle.location.copy()
    t.begin_path()
    t.fd(d=b)
    loc_B = turtle.location.copy()
    t.rt(d=180 - C)
    t.fd(d=a)
    loc_C = turtle.location.copy()
    t.rt(d=180 - B)
    t.fd(d=c)

    t.select_all()
    t.merge()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.subdivide(number_cuts=native_subdivisions[0])

    i = 0
    while i < native_subdivisions[1]:
        t.up(d=height / native_subdivisions[1])
        i += 1

    bpy.ops.mesh.inset(thickness=0.001, depth=0)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()

    dimensions = {
        'a': a,  # sides
        'b': b,
        'c': c,
        'A': A,  # angles
        'B': B,
        'C': C,
        'loc_A': loc_A,  # corner coords
        'loc_B': loc_B,
        'loc_C': loc_C}

    return bpy.context.object, dimensions