from math import sqrt, radians, degrees, cos, acos
import bpy
from ...utils.utils import mode
from ...utils.selection import deselect_all

outer_w = 0.2362                 # outer ring width
slot_w = 0.1811                # slot width
slot_h = 0.2402                # slot height
support_w = 0.11811              # slot support width
support_h = 0.05472            # slot support height
extra_sup_dist = 0.8531       # distance between extra supports for large tiles


def distance_between_two_verts(first, second):
    '''returns the distance between 2 verts'''
    locx = second[0] - first[0]
    locy = second[1] - first[1]
    locz = second[2] - first[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)

    return distance


def draw_openlock_pos_curved_base(length, segments, angle, height):
    t = bpy.ops.turtle
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    # draw outer loop
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

    bpy.ops.object.editmode_toggle()

    # save outer loop vert indices
    outer_loop = []
    for vert in bpy.context.object.data.vertices:
        if vert.select is True:
            outer_loop.append(vert.index)
    bpy.ops.object.editmode_toggle()
    t.deselect_all()
    t.pu()

    # draw loop 2
    # first draw two temporary edges inside and parallel to the
    # outer loop at the appropriate distance
    t.rt(d=angle)
    t.fd(d=length / 2)
    t.lt(d=90)
    t.fd(d=outer_w)
    t.lt(d=90)
    t.pd()
    t.add_vert()
    t.begin_path()
    t.fd(d=0.01)
    t.deselect_all()
    t.pu()
    t.home()
    t.fd(d=length / 2)
    t.rt(d=90)
    t.fd(d=outer_w)
    t.rt(d=90)
    t.pd()
    t.add_vert()
    t.fd(d=0.01)
    t.select_path()

    # add vert at projected intersection of last two edges
    bpy.ops.maketile.vertintersect()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    # save vert location
    new_vert_loc = bpy.context.object.data.vertices[len(bpy.context.object.data.vertices) - 1].co.copy()
    bpy.ops.mesh.delete(type='VERT')

    # move to new vert location and reset rotation
    t.set_position(v=new_vert_loc)
    t.set_rotation(v=(0, 0, 0))

    # calculate distance between current location and origin of outer loop
    dist = distance_between_two_verts(new_vert_loc, origin)

    # work out length of loop 2 edge
    length_2 = length - dist - outer_w

    # draw arc
    t.arc(r=length_2, d=angle, s=segments)

    # add vert and connect up new loop's origin to arc then bridge between two loops
    t.add_vert()
    t.pd()
    t.fd(d=length_2)
    t.deselect_all()
    t.set_position(v=new_vert_loc)
    t.select_at_cursor()
    t.rt(d=angle)
    t.fd(d=length_2)
    t.select_all()
    t.merge(t=0.01)
    t.bridge()

    # save loop 2 vert indices
    loop_2 = []
    for vert in bpy.context.object.data.vertices:
        if vert.index not in outer_loop:
            loop_2.append(vert.index)

    t.deselect_all()

    outer_vert_count = len(bpy.context.object.data.vertices)

    # draw loop 3 using same method as loop 2
    t.set_position(v=new_vert_loc)
    t.set_rotation(v=(0, 0, 0))

    t.rt(d=angle)
    t.fd(d=length_2 / 2)
    t.lt(d=90)
    t.fd(d=slot_w)
    t.lt(d=90)
    t.pd()
    t.add_vert()
    t.begin_path()
    t.fd(d=0.01)
    t.deselect_all()
    t.pu()
    t.set_position(v=new_vert_loc)
    t.set_rotation(v=(0, 0, 0))
    t.fd(d=length_2 / 2)
    t.rt(d=90)
    t.fd(d=slot_w)
    t.rt(d=90)
    t.pd()
    t.add_vert()
    t.fd(d=0.01)
    t.select_path()
    bpy.ops.maketile.vertintersect()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    new_vert_2_loc = bpy.context.object.data.vertices[len(bpy.context.object.data.vertices) - 1].co.copy()
    bpy.ops.mesh.delete(type='VERT')
    t.set_position(v=new_vert_2_loc)
    t.set_rotation(v=(0, 0, 0))
    dist = distance_between_two_verts(new_vert_loc, new_vert_2_loc)
    length_3 = length_2 - dist - slot_w
    t.arc(r=length_3, d=angle, s=segments)
    t.add_vert()
    t.pd()
    t.fd(d=length_3)
    t.deselect_all()
    t.set_position(v=new_vert_2_loc)
    t.select_at_cursor()
    t.rt(d=angle)
    t.fd(d=length_3)
    t.select_all()
    t.merge(t=0.01)
    t.deselect_all()
    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index not in outer_loop:
            vert.select = True

    bpy.ops.object.editmode_toggle()

    # add face to inner loop
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()
    bpy.ops.object.editmode_toggle()

    # select inner loop
    for vert in bpy.context.object.data.vertices:
        if vert.index not in outer_loop and vert.index not in loop_2:
            vert.select = True

    bpy.ops.object.editmode_toggle()

    # extrude inner loop up
    t.pd()
    t.up(d=slot_h)

    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()

    # save inner loop top verts
    inner_top_verts = []
    for vert in bpy.context.object.data.vertices:
        if vert.select is True:
            inner_top_verts.append(vert.index)

    # delete top face
    bpy.ops.mesh.delete(type='ONLY_FACE')

    bpy.ops.object.editmode_toggle()

    # select loop 2 and extrude up
    for vert in bpy.context.object.data.vertices:
        if vert.index in loop_2:
            vert.select = True

    bpy.ops.object.editmode_toggle()
    t.up(d=slot_h)
    bpy.ops.object.editmode_toggle()

    for vert in bpy.context.object.data.vertices:
        if vert.index in inner_top_verts:
            vert.select = True

    bpy.ops.object.editmode_toggle()
    # bridge between loop 2 top and inner loop top
    t.bridge()
    t.deselect_all()
    bpy.ops.object.editmode_toggle()

    # select outer loop extrude up and add face
    for vert in bpy.context.object.data.vertices:
        if vert.index in outer_loop:
            vert.select = True
    bpy.ops.object.editmode_toggle()
    t.up(d=height)
    bpy.ops.mesh.edge_face_add()

    t.select_all()

    # clean up
    bpy.ops.mesh.normals_make_consistent()
    t.deselect_all()
    t.home()
    t.select_all()
    bpy.ops.mesh.quads_convert_to_tris(
        quad_method='BEAUTY',
        ngon_method='BEAUTY')

    mode('OBJECT')
    base = bpy.context.object
    deselect_all()

    return base


def draw_pos_curved_slab(length, segments, angle, height, native_subdivisions=1):
    t = bpy.ops.turtle

    mode('OBJECT')
    t.add_turtle()
    t.pd()

    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=length / native_subdivisions[0])
        i += 1

    t.pu()
    t.home()
    t.deselect_all()
    t.select_at_cursor()
    t.pd()
    t.rt(d=angle)

    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=length / native_subdivisions[0])
        i += 1

    t.home()
    t.deselect_all()
    t.arc(r=length, d=angle, s=segments)
    t.select_all()
    t.merge(t=0.01)
    bpy.ops.mesh.fill_grid(span=native_subdivisions[0])
    t.pd()
    t.up(d=height)
    bpy.ops.mesh.inset(thickness=0.001, depth=0)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()
    t.select_all()
    mode('OBJECT')
    slab = bpy.context.object
    deselect_all()

    return slab

def draw_neg_curved_slab(length, segments, angle, height, native_subdivisions, return_vert_locs=False):
    t = bpy.ops.turtle
    start_loc = bpy.context.scene.cursor.location.copy()
    dim = calc_tri(angle, length, length)

    mode('OBJECT')
    t.add_turtle()
    t.pd()
    t.add_vert()
    verts = bpy.context.object.data.vertices
    vert_locs = {}

    # draw side b
    side_b_vert_locs = []
    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=length / native_subdivisions[0])
        i += 1
    for v in verts:
        side_b_vert_locs.append(v.co.copy())
    vert_locs['side_b'] = side_b_vert_locs
    t.pu()
    t.home()
    t.deselect_all()
    t.select_at_cursor()
    t.pd()

    # draw side c
    t.rt(d=angle)
    side_c_vert_locs = []

    start_index = verts.values()[-1].index
    i = 0
    while i < native_subdivisions[0]:
        t.fd(d=length / native_subdivisions[0])
        i += 1

    i = start_index
    while i <= verts.values()[-1].index:
        side_c_vert_locs.append(verts[i].co.copy())
        i += 1

    vert_locs['side_c'] = side_c_vert_locs
    t.deselect_all()
    t.pu()

    # move to opposite of angle A on mirror triangle
    t.lt(d=180 - dim['C'] * 2)
    t.fd(d=length)
    t.lt(d=180)

    # draw side a
    side_a_vert_locs = []
    start_index = verts.values()[-1].index
    t.arc(r=length, d=angle, s=segments)

    i = start_index
    while i < verts.values()[-1].index:
        side_a_vert_locs.append(verts[i].co.copy())
        i += 1
    side_a_vert_locs.append(verts[verts.values()[-1].index].co.copy())
    vert_locs['side_a'] = side_a_vert_locs

    t.pu()
    t.deselect_all()
    t.home()
    t.fd(d=length)
    t.select_at_cursor()
    bpy.ops.mesh.merge(type='CURSOR')
    t.select_all()
    t.merge(t=0.01)
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=height)  
    bpy.ops.mesh.inset(thickness=0.001, depth=0)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    t.pu()
    t.home()

    bpy.ops.mesh.quads_convert_to_tris(
        quad_method='BEAUTY',
        ngon_method='BEAUTY')

    mode('OBJECT')
    slab = bpy.context.object
    deselect_all()

    if return_vert_locs is True:
        return slab, vert_locs

    return slab


def calc_tri(A, b, c):
    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    dimensions = {
        'a': a,
        'B': B,
        'C': C}

    return dimensions
