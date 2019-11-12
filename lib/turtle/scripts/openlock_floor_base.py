from math import floor, sqrt
import bpy
from mathutils import *
outer_w = 6                 # outer ring width
slot_w = 4.6                # slot width
slot_h = 6.1                # slot height
support_w = 3               # slot support width
support_h = 1.39            # slot support height
extra_sup_dist = 23.4       # distance between extra supports for large tiles


def draw_floor(dimensions):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    x = dimensions[0]
    y = dimensions[1]
    z = dimensions[2]

    t.add_turtle()

    # We want our tile to have its origin at the center
    # so we make sure the pen is up
    # and move the cursor back along the Y axis by 0.5 Y
    t.pu()
    t.bk(d=y / 2)
    t.pd()
    t.add_vert()
    start_loc = turtle.location.copy()
    draw_quarter_floor(dimensions, start_loc)
    base = bpy.context.object
    mirror_mod = base.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = True
    mirror_mod.use_axis[1] = True


def draw_quarter_floor(dimensions, start_loc):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    x = dimensions[0]
    y = dimensions[1]
    z = dimensions[2]

    # draw loop 1
    t.ri(d=x / 2)
    t.fd(d=y / 2)

    # move turtle
    t.pu()
    t.deselect_all()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.pd()
    
    # draw loop 2
    t.add_vert()
    t.begin_path()
    t.ri(d=x / 2 - outer_w)
    t.fd(d=y / 2 - outer_w)
    t.select_path()
    
    # create bevel for corner supports
    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=3, offset_pct=0, vertex_only=True)

    # move turtle
    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w + slot_w)
    t.pd()

    # draw loop 3
    t.add_vert()
    t.begin_path()
    t.ri(d= x / 2 - slot_w - outer_w)
    t.fd(d= y / 2 - slot_w - outer_w)
    t.select_path()
    
    # create bevel for corner supports
    bpy.ops.mesh.bevel(offset_type='WIDTH', offset=3, offset_pct=0, vertex_only=True)

    #bridge bevels
    leg = support_w / sqrt(2)
    t.pu()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w + slot_w)
    t.ri(d=x / 2 - outer_w - slot_w - leg)

    t.select_at_cursor()
    t.bk(d=slot_w)
    t.ri(d=slot_w)
    t.select_at_cursor()
    t.ri(d=leg)
    t.fd(d=leg)
    t.select_at_cursor()

    t.fd(d=slot_w)
    t.lf(d=slot_w)
    t.select_at_cursor()
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()
    t.select_at_cursor()
    t.lf(d=leg)   
    t.bk(d=leg)
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='EDGE')

    t.bk(d=slot_w)
    t.ri(d=slot_w)
    t.select_at_cursor()
    t.fd(d=leg)
    t.ri(d=leg)
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='EDGE')
    

    # check if either side is greater than 101.6mm (4").
    # if yes we add some extra support between outer and inner ring
    if x >= 101.6:
        x_supports = 1 + floor((x - 101.6) / 50.8)
    else: x_supports = 0

    if y >= 101.6:
        y_supports = 1 + floor((y - 101.6) / 50.8)
    else: y_supports = 0

    t.home()
    t.pu()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.rt(d=90) 
   
    if x_supports > 0:
        add_extra_supports(x_supports, 'x', support_w, slot_w, x, y, leg, outer_w, start_loc, side_length = x)

    t.home()
    t.ri(d=x / 2 - outer_w)
    t.rt(d=180)

    if y_supports > 0:
        add_extra_supports(y_supports, 'y', support_w, -slot_w, x, y, leg, -outer_w, start_loc, side_length = y)

    # extrude inner sides up
    t.pd()
    t.select_all()
    t.up(d=support_h)
    t.select_all()
    t.merge()
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)

    #join outer edges
    t.pd()    
    t.select_at_cursor()
    t.fd(d=outer_w)
    t.deselect_all()
    t.pu()
    t.fd(d=slot_w)  
    t.pd()
    t.select_at_cursor()
    t.fd(d=y / 2 - slot_w - outer_w)
    t.ri(d = x / 2 - slot_w - outer_w)
    t.pu()
    t.deselect_all()
    t.ri(d=slot_w)
    t.pd()
    t.select_at_cursor()
    t.ri(d=outer_w)
    t.select_all()
    t.merge()

    # fill base
    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.select_by_location(
            lbound=turtle.location, 
            ubound=(turtle.location[0] + x / 2,
                    turtle.location[1] + y / 2,
                    turtle.location[2]))
               
    bpy.ops.mesh.fill()
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()


    # draw extra support roofs
    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.rt(d=90) 
    t.up(d=support_h)
 
    if x_supports > 0:
        fill_extra_supports(x_supports, 'x', support_w, slot_w)
  
    t.home()
    t.ri(d=x / 2 - outer_w)
    t.rt(d=180)
    t.up(d=support_h)
    
    if y_supports > 0:
        fill_extra_supports(y_supports, 'y', support_w, -slot_w)
    
    # draw corner support roofs
    t.deselect_all()
    t.pu
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.up(d=support_h)
    t.ri(d=x / 2 - outer_w - leg)
    t.select_at_cursor()
    t.ri(d=leg)
    t.fd(d=leg)
    t.select_at_cursor()
    t.fd(d=slot_w)
    t.lf(d=slot_w)
    t.select_at_cursor()
    t.lf(d=leg)
    t.bk(d=leg)
    t.select_at_cursor()
    bpy.ops.mesh.edge_face_add()

  
    #bridge_slot
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.up(d=support_h)
    t.select_at_cursor()
    t.pd()
    t.fd(d=slot_w)
    t.deselect_all()
    t.pu()
    t.ri(d=x / 2 - outer_w - slot_w)
    t.fd(d=y / 2 - outer_w - slot_w)
    t.select_at_cursor()
    t.pd()
    t.ri(d=slot_w)
    t.pu()

    #draw duplicate top of supports and slot
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.up(d=support_h)
    t.select_by_location(
                lbound=turtle.location,
                ubound=(turtle.location[0] + x / 2 - outer_w,
                        turtle.location[1] + y / 2 - outer_w,
                        turtle.location[2]))
    
    bpy.ops.mesh.duplicate_move(
        TRANSFORM_OT_translate={
                    "value": (0, 0, slot_h - support_h),
                    "orient_type": 'CURSOR'})
    t.merge()
    bpy.ops.mesh.edge_face_add()
    

    # extrude down and clean
    t.pd()
    t.dn(d=slot_h - support_h)
    bpy.ops.mesh.delete(type='FACE')

    # clean non-manifolds at end
    t.pu()
    t.deselect_all()
    t.home()
    t.set_position(v=start_loc)
    t.fd(d=outer_w)
    t.up(d=support_h)
    t.select_at_cursor()
    t.fd(d=slot_w)
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='EDGE')
    t.ri(d= x / 2 - outer_w)
    t.fd(d=y / 2 - outer_w - slot_w)
    t.select_at_cursor()
    t.lf(d=slot_w)
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='EDGE')

    # draw outer wall
    t.pu()
    t.home()
    t.set_position(v=start_loc)
    t.up(d=support_h)
    t.select_at_cursor()
    t.ri(d=x / 2)
    t.select_at_cursor()
    t.fd(d=y / 2)
    t.select_at_cursor()
    t.pd()
    t.up(d=z - support_h)

    # draw top
    t.pu()
    t.deselect_all()
    t.home()
    t.up(d=z)
    t.pd()  
    t.add_vert()
    t.begin_path()
    t.ri(d=x / 2)
    t.select_path()
    t.bk(d=y / 2)

    #clean up
    t.select_all()
    t.merge()
    bpy.ops.mesh.normals_make_consistent()
    t.deselect_all()
    t.home()
      
    
def add_extra_supports(num_supports, axis, support_w, slot_w, x, y, leg, outer_w, start_loc, side_length):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='VERT')
    t.lf(d=slot_w)
    t.select_at_cursor()
    bpy.ops.mesh.delete(type='VERT')
    t.pd()
    t.add_vert()
    t.fd(d=extra_sup_dist / 2)
    t.ri(d=slot_w)
    t.bk(d=extra_sup_dist / 2)
    t.deselect_all()
    t.pu()
    t.fd(d=(extra_sup_dist / 2) + support_w)
    
    for i in range(num_supports-1):
        t.pd()
        t.add_vert()
        t.begin_path()
        t.fd(d=extra_sup_dist)
        t.lf(d=slot_w)
        t.bk(d=extra_sup_dist)
        t.stroke_path()
        t.pu()
        t.deselect_all()
        t.ri(d=slot_w)
        t.fd(d=extra_sup_dist+support_w)

    if axis == 'x':        
        a = num_supports * extra_sup_dist
        b = extra_sup_dist / 2
        c = support_w * (num_supports+1)
        d = outer_w + leg
        
        t.pd()
        t.add_vert()

        if num_supports > 1:
            t.fd(d=side_length /2 - a + b - c - d + support_w)
            t.pu()
            t.deselect_all()
            t.bk(d=side_length /2 - a + b - c - d + support_w)
            t.select_at_cursor()
            t.pd()
            t.lf(d=slot_w)
            t.fd(d=side_length /2 - a + b- c - d - slot_w + support_w)
        else:
            t.fd(d=side_length / 2 - b - d - support_w)
            t.pu()
            t.deselect_all()
            t.bk(d=side_length / 2 - b - d - support_w)
            t.select_at_cursor()
            t.pd()
            t.lf(d=slot_w)
            t.fd(d=side_length / 2 - b - d - support_w - slot_w)
            
        t.select_all()
        t.merge()
        t.deselect_all()
        t.pu()
        
    else:
        a = extra_sup_dist * (num_supports-1) - support_w
        b = extra_sup_dist / 2
        c = support_w * (num_supports+1)
        d = outer_w - leg
        
        t.pd()
        t.add_vert()

        if num_supports > 1:
            t.fd(d=side_length /2  - a - b - c + d )
            t.pu()
            t.deselect_all()
            t.bk(d=side_length /2  - a - b - c + d )
            t.select_at_cursor()
            t.pd()
            t.lf(d=slot_w)
            t.fd(d=side_length /2  - a - b - c + d + slot_w)
 
        else:
            t.fd(d=side_length / 2  - b - support_w +d)
            t.pu()
            t.deselect_all()
            t.bk(d=side_length / 2  - b - support_w +d)
            t.select_at_cursor()
            t.pd()
            t.lf(d=slot_w)
            t.fd(d=side_length / 2  - b - support_w + d + slot_w)

        t.select_all()
        t.merge()
        t.deselect_all()
        t.pu()

    
def fill_extra_supports(num_supports, axis, support_w, slot_w):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.fd(d=extra_sup_dist / 2)
    t.select_at_cursor()
    t.lf(d=slot_w)
    t.select_at_cursor()
    t.fd(d=support_w)
    t.select_at_cursor()
    t.ri(d=slot_w)
    t.select_at_cursor()
    bpy.ops.mesh.edge_face_add()
    t.deselect_all()
    for i in range(num_supports - 1):
        t.fd(d=extra_sup_dist)
        t.select_at_cursor()
        t.lf(d=slot_w)
        t.select_at_cursor()
        t.fd(d=support_w)
        t.select_at_cursor()
        t.ri(d=slot_w)
        t.select_at_cursor()
        bpy.ops.mesh.edge_face_add()
        t.deselect_all()
