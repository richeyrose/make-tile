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
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    loc_A = turtle.location.copy()
    t.begin_path()
    t.fd(d=b)
    loc_B = turtle.location.copy()
    t.rt(d=180 - C)
    t.fd(d=a)
    loc_C = turtle.location.copy()
    t.rt(d=180 - B)
    t.fd(d=c)
    t.select_path()
    t.merge()
    t.pu()
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


def draw_tri_prism(b, c, A, height):
    '''draws a triangular prism given the length of two sides of triangle (a, b),
    the angle between them (A) and the height'''

    triangle = draw_triangle(b, c, A)

    t = bpy.ops.turtle
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    return bpy.context.object
