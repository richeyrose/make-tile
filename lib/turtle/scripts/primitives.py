import bpy
from math import sqrt, cos, radians, acos, degrees


# TODO: make it consistent whether we add turtle in script or prior
def draw_cuboid(size):
    """Returns a cuboid. size = (x, y, z)"""
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    t.add_turtle()
    t.pd()
    t.add_vert()
    t.begin_path()
    t.ri(d=size[0])
    t.fd(d=size[1])
    t.lf(d=size[0])
    t.fill_path()
    t.select_all()
    t.up(d=size[2])
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    return bpy.context.object


def draw_triangle(b, c, A):
    '''draws a triangle given the length of two sides (a, b) and the angle between them (A)'''
    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    t = bpy.ops.turtle
    t.begin_path()
    t.fd(d=b)
    t.rt(d=180 - C)
    t.fd(d=a)
    t.rt(d=180 - B)
    t.fd(d=c)
    t.select_path()
    t.merge()
    t.pu()
