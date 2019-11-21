import bpy


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
    return bpy.context.object
