import bpy
from math import sqrt, pi, degrees, radians


def draw_openlock_curved_base(radius, segments, angle, height, clip_side):
    t = bpy.ops.turtle
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    base_width = 0.5
    slot_outer_dist = 0.071
    slot_side_dist = 0.236
    slot_w = 0.1811
    slot_h = 0.2402

    inner_circ = 2 * pi * radius
    outer_circ = 2 * pi * (radius + base_width)

    # draw inner radius loop
    t.add_turtle()
    t.pd()

    t.arc(r=radius, d=angle, s=segments)

    # save inner loop vert indices
    inner_loop = []
    for vert in bpy.context.object.data.vertices:
        inner_loop.append(vert.index)

    t.arc(r=radius + base_width, d=angle, s=segments)

    outer_loop = []

    for vert in bpy.context.object.data.vertices:
        if vert.index not in inner_loop:
            outer_loop.append(vert.index)
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.delete(type='ONLY_FACE')

    if clip_side == 'INNER':
        slot_outer_radius = radius + base_width - slot_outer_dist
        slot_inner_radius = radius + base_width - slot_outer_dist - slot_w
    else:
        slot_outer_radius = radius + slot_outer_dist
        slot_inner_radius = radius + slot_outer_dist + slot_w

    slot_outer_arc_len = (2 * pi * slot_outer_radius) / (360 / angle) - (slot_side_dist * 2)
    central_angle = degrees(slot_outer_arc_len / slot_outer_radius)
    t.rt(d=(angle - central_angle) / 2)
    t.arc(r=slot_outer_radius, d=central_angle, s=segments)

    slot_inner_radius = radius + base_width - slot_outer_dist - slot_w
    slot_inner_arc_len = (2 * pi * slot_inner_radius) / (360 / angle) - (slot_side_dist * 2)
    central_angle = degrees(slot_inner_arc_len / slot_inner_radius)
    t.home()
    t.rt(d=(angle - central_angle) / 2)
    t.arc(r=slot_inner_radius, d=central_angle, s=segments)

    slot_loop = []

    for vert in bpy.context.object.data.vertices:
        if vert.index not in inner_loop and vert.index not in outer_loop:
            slot_loop.append(vert.index)

    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index in slot_loop:
            vert.select = True

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.delete(type='ONLY_FACE')

    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index in slot_loop:
            vert.select = True

    bpy.ops.object.editmode_toggle()

    t.pd()
    t.up(d=slot_h)
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()

    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index in slot_loop or vert.index in inner_loop or vert.index in outer_loop:
            vert.select = True

    bpy.ops.object.editmode_toggle()

    t.bridge()
    t.deselect_all()

    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index in inner_loop or vert.index in outer_loop:
            vert.select = True

    bpy.ops.object.editmode_toggle()
    t.pd()
    t.up(d=height)
    bpy.ops.mesh.edge_face_add()

    t.select_all()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.normals_make_consistent()

    t.home()
    bpy.ops.object.editmode_toggle()

    return bpy.context.object
