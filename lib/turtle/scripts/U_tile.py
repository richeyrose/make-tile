import bpy
from ... utils.selection import select_by_loc
from ... utils.utils import mode


def draw_u_3D(leg_1_len, leg_2_len, thickness, height, inner_len, inc_vert_locs=False):
    '''Returns a 3D U shape and optionally locations of bottom verts'''
    vert_loc = draw_u_2D(leg_1_len, leg_2_len, thickness, inner_len)

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


def draw_u_2D(leg_1_len, leg_2_len, thickness, inner_len):
    '''
    leg_1_len and leg_2_len are the inner lengths of the legs
                ||           ||
                ||leg_1 leg_2||
                ||           ||
                ||___inner___||
         origin x--------------
                     outer
    '''
    leg_1_outer_len = leg_1_len + thickness
    leg_2_outer_len = leg_2_len + thickness
    outer_len = inner_len + (thickness * 2)

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
    # draw leg_1
    t.fd(d=0.001)
    vert_loc['leg_1_1'] = turtle.location.copy()
    t.fd(d=leg_1_outer_len - 0.002)
    vert_loc['leg_1_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['leg_1_3'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['leg_1_4'] = turtle.location.copy()
    t.fd(d=thickness - 0.002)
    vert_loc['leg_1_5'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['leg_1_6'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['leg_1_7'] = turtle.location.copy()
    t.fd(d=leg_1_len - 0.001)
    vert_loc['leg_1_8'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=inner_len)
    vert_loc['leg_2_1'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=leg_2_len - 0.001)
    vert_loc['leg_2_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['leg_2_3'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['leg_2_4'] = turtle.location.copy()
    t.fd(d=thickness - 0.002)
    vert_loc['leg_2_5'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['leg_2_6'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['leg_2_7'] = turtle.location.copy()
    t.fd(d=leg_2_outer_len - 0.002)
    vert_loc['leg_2_8'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['leg_2_9'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['outer_1'] = turtle.location.copy()
    t.fd(d=outer_len - 0.002)
    vert_loc['outer_2'] = turtle.location.copy()
    t.fd(d=0.001)

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()

    # connect leg_1_2 and leg_1_7 so we can have flat ends
    select_by_loc(
        lbound=vert_loc['leg_1_2'],
        ubound=vert_loc['leg_1_2'],
        buffer=0.0001)

    select_by_loc(
        lbound=vert_loc['leg_1_7'],
        ubound=vert_loc['leg_1_7'],
        buffer=0.0001,
        additive=True)

    bpy.ops.mesh.vert_connect_path()
    t.deselect_all()

    # connect leg_2_2 and leg_2_7
    select_by_loc(
        lbound=vert_loc['leg_2_2'],
        ubound=vert_loc['leg_2_2'],
        buffer=0.0001)

    select_by_loc(
        lbound=vert_loc['leg_2_7'],
        ubound=vert_loc['leg_2_7'],
        buffer=0.0001,
        additive=True)

    bpy.ops.mesh.vert_connect_path()
    t.deselect_all()

    mode('OBJECT')
    return vert_loc
