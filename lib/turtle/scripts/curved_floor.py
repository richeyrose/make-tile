import bpy
from math import sqrt, radians, degrees, cos, acos
from ... utils.utils import mode


def draw_pos_curved_slab(length, segments, angle, height):
    t = bpy.ops.turtle
    turtle = bpy.context.scene.cursor

    mode('OBJECT')
    t.add_turtle()
    t.pd()
    t.fd(d=length)
    t.pu()
    t.home()
    t.deselect_all()
    t.select_at_cursor()
    t.pd()
    t.rt(d=angle)
    t.fd(d=length)
    t.home()
    t.deselect_all()
    t.arc(r=length, d=angle, s=segments)
    t.select_all()
    t.merge(t=0.01)
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    mode('OBJECT')


def draw_neg_curved_slab(length, segments, angle, height):
    t = bpy.ops.turtle
    turtle = bpy.context.scene.cursor

    dim = calc_tri(angle, length, length)

    mode('OBJECT')
    t.add_turtle()
    t.pd()
    t.fd(d=length)
    t.pu()
    t.home()
    t.deselect_all()
    t.select_at_cursor()
    t.pd()
    t.rt(d=angle)
    t.fd(d=length)
    t.deselect_all()
    t.pu()
    t.lt(d=180 - dim['C'] * 2)
    t.fd(d=length)
    t.lt(d=180)
    t.arc(r=length, d=angle, s=segments)
    t.select_all()
    t.merge(t=0.01)
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    mode('OBJECT')


def calc_tri(A, b, c):
    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    dimensions = {
        'a': a,
        'B': B,
        'C': C}

    return dimensions
