import bpy


def draw_rectangular_floor_core(size, native_subdivisions):
    t = bpy.ops.turtle

    t.add_turtle()
    t.pd()
    t.ri(d=0.001)

    subdiv_x_dist = (size[0] - 0.002) / native_subdivisions[0]

    i = 0
    while i < native_subdivisions[0]:
        t.ri(d=subdiv_x_dist)
        i += 1

    t.ri(d=0.001)

    t.select_all()
    t.fd(d=0.001)
    subdiv_y_dist = (size[1] - 0.002) / native_subdivisions[1]

    i = 0
    while i < native_subdivisions[1]:
        t.fd(d=subdiv_y_dist)
        i += 1

    t.fd(d=0.001)

    t.select_all()
    t.up(d=0.001)
    subdiv_z_dist = (size[2] - 0.002) / native_subdivisions[2]

    i = 0
    while i < native_subdivisions[2]:
        t.up(d=subdiv_z_dist)
        i += 1

    t.up(d=0.001)

    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    bpy.ops.object.mode_set(mode='OBJECT')

    return bpy.context.object


def draw_straight_floor_core(size, native_subdivisions):
    t = bpy.ops.turtle

    t.add_turtle()
    t.pd()
    t.ri(d=0.001)

    subdiv_x_dist = (size[0] - 0.002) / native_subdivisions[0]

    i = 0
    while i < native_subdivisions[0]:
        t.ri(d=subdiv_x_dist)
        i += 1

    t.ri(d=0.001)

    t.select_all()
    t.fd(d=0.001)
    subdiv_y_dist = (size[1] - 0.002) / native_subdivisions[1]

    i = 0
    while i < native_subdivisions[1]:
        t.fd(d=subdiv_y_dist)
        i += 1

    t.fd(d=0.001)

    t.select_all()
    t.up(d=0.001)

    subdiv_z_dist = (size[2] - 0.002) / native_subdivisions[2]

    i = 0
    while i < native_subdivisions[2]:
        t.up(d=subdiv_z_dist)
        i += 1

    t.up(d=0.001)

    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    bpy.ops.object.mode_set(mode='OBJECT')

    return bpy.context.object


def draw_straight_wall_core(size, native_subdivisions):
    t = bpy.ops.turtle

    t.add_turtle()
    t.pd()
    t.add_vert()
    t.ri(d=0.001)

    subdiv_x_dist = (size[0] - 0.002) / native_subdivisions[0]
    i = 0
    while i < native_subdivisions[0]:
        t.ri(d=subdiv_x_dist)
        i += 1

    t.ri(d=0.001)
    t.select_all()
    t.fd(d=0.001)

    subdiv_y_dist = (size[1] - 0.002) / native_subdivisions[1]

    i = 0
    while i < native_subdivisions[1]:
        t.fd(d=subdiv_y_dist)
        i += 1

    t.fd(d=0.001)
    t.select_all()
    t.up(d=0.001)

    subdiv_z_dist = (size[2] - 0.002) / native_subdivisions[2]

    i = 0
    while i < native_subdivisions[2]:
        t.up(d=subdiv_z_dist)
        i += 1

    t.up(d=0.001)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    bpy.ops.object.mode_set(mode='OBJECT')

    return bpy.context.object
