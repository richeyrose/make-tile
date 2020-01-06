import bpy
from .. lib.utils.selection import select, deselect_all, select_all, activate
from .. lib.utils.utils import mode, add_deform_modifiers, calc_tri
from mathutils import Vector
from .. lib.turtle.scripts.primitives import draw_cuboid, draw_tri_prism, draw_curved_slab
from math import radians


# works for rectangular floors and straight walls
def create_cuboid_tile_trimmers(
        tile_size,
        base_size,
        tile_name,
        base_blueprint,
        tile_empty):

    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()

    # create a cuboid the size of our tile and center it to use
    # as our bounding box for entire tile
    if base_blueprint is not 'NONE':
        bbox_proxy = draw_cuboid(Vector((
            tile_size[0],
            base_size[1],
            tile_size[2])))
    else:
        bbox_proxy = draw_cuboid(tile_size)

    bbox_proxy.location = (
        bbox_proxy.location[0] - bbox_proxy.dimensions[0] / 2,
        bbox_proxy.location[1] - bbox_proxy.dimensions[1] / 2,
        bbox_proxy.location[2])

    ctx = {
        'selected_objects': [bbox_proxy]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    # get bounding box and dimensions of cuboid
    bound_box = bbox_proxy.bound_box
    dimensions = bbox_proxy.dimensions.copy()

    # create trimmers
    buffer = bpy.context.scene.mt_trim_buffer
    x_neg_trimmer = create_x_neg_trimmer(bound_box, dimensions, buffer)
    x_neg_trimmer.name = 'X Neg Trimmer.' + tile_name
    x_pos_trimmer = create_x_pos_trimmer(bound_box, dimensions, buffer)
    x_pos_trimmer.name = 'X Pos Trimmer.' + tile_name
    y_neg_trimmer = create_y_neg_trimmer(bound_box, dimensions, buffer)
    y_neg_trimmer.name = 'Y Neg Trimmer.' + tile_name
    y_pos_trimmer = create_y_pos_trimmer(bound_box, dimensions, buffer)
    y_pos_trimmer.name = 'Y Pos Trimmer.' + tile_name
    z_pos_trimmer = create_z_pos_trimmer(bound_box, dimensions, buffer)
    z_pos_trimmer.name = 'Z Pos Trimmer.' + tile_name
    z_neg_trimmer = create_z_neg_trimmer(bound_box, dimensions, buffer)
    z_neg_trimmer.name = 'Z Neg Trimmer.' + tile_name

    trimmers = [x_neg_trimmer,
                x_pos_trimmer,
                y_neg_trimmer,
                y_pos_trimmer,
                z_pos_trimmer,
                z_neg_trimmer]

    cursor.location = cursor_orig_location

    save_trimmer_props(trimmers, tile_empty, tile_name)

    bpy.ops.object.delete({"selected_objects": [bbox_proxy]})

    return trimmers


def create_curved_wall_tile_trimmers(tile_size, base_size, tile_name, base_blueprint, tile_empty):
    deselect_all()

    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()
    tile_props = bpy.context.collection.mt_tile_props

    # create a cuboid the size of our tile and center it to use
    # as our bounding box for entire tile for Z trimmers
    if base_blueprint is not 'NONE':
        if tile_props.degrees_of_arc > 0:
            bbox_size = Vector((
                tile_size[0],
                base_size[1],
                tile_size[2]))
        else:
            bbox_size = Vector((
                tile_size[0] * -1,
                base_size[1],
                tile_size[2]))

        bbox_proxy = draw_cuboid(bbox_size)
    else:
        if tile_props.degrees_of_arc > 0:
            bbox_size = tile_size
        else:
            bbox_size = Vector((
                tile_size[0] * -1,
                tile_size[1],
                tile_size[2]))

        bbox_proxy = draw_cuboid(bbox_size)

    mode('OBJECT')

    if tile_props.degrees_of_arc > 0:
        bbox_proxy.location = (
            bbox_proxy.location[0] - bbox_proxy.dimensions[0] / 2,
            bbox_proxy.location[1] - bbox_proxy.dimensions[1] / 2,
            bbox_proxy.location[2])
    else:
        bbox_proxy.location = (
            bbox_proxy.location[0] - bbox_proxy.dimensions[0] / 2,
            bbox_proxy.location[1] - bbox_proxy.dimensions[1] / 4,
            bbox_proxy.location[2])

    cursor.location = cursor_orig_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    # get bounding box and dimensions of cuboid
    bound_box = bbox_proxy.bound_box
    dimensions = bbox_proxy.dimensions.copy()

    buffer = bpy.context.scene.mt_trim_buffer

    # create x trimmers
    x_pos_trimmer = draw_cuboid(Vector((
        1,
        tile_size[1] + 1,
        tile_size[2] + 1)))

    x_pos_trimmer.name = 'X Pos Trimmer.' + tile_name

    mode('OBJECT')
    x_pos_trimmer.location = (
        x_pos_trimmer.location[0],
        x_pos_trimmer.location[1] - x_pos_trimmer.dimensions[1] / 2,
        x_pos_trimmer.location[2] - 0.5)
    cursor.location = cursor_orig_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    if tile_props.degrees_of_arc > 0:
        circle_center = Vector((
            x_pos_trimmer.location[0],
            x_pos_trimmer.location[1] + tile_props.wall_radius,
            x_pos_trimmer.location[2]))
    else:
        circle_center = Vector((
            x_pos_trimmer.location[0],
            x_pos_trimmer.location[1] - tile_props.wall_radius,
            x_pos_trimmer.location[2]))

    bpy.ops.transform.rotate(
        value=-radians((tile_props.degrees_of_arc / 2)),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    x_neg_trimmer = draw_cuboid(Vector((-1, tile_size[1] + 1, tile_size[2] + 1)))
    x_neg_trimmer.name = 'X Neg Trimmer.' + tile_name
    mode('OBJECT')
    x_neg_trimmer.location = (
        x_neg_trimmer.location[0],
        x_neg_trimmer.location[1] - x_neg_trimmer.dimensions[1] / 2,
        x_neg_trimmer.location[2] - 0.5)
    cursor.location = cursor_orig_location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.transform.rotate(
        value=radians(tile_props.degrees_of_arc / 2),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    mode('OBJECT')

    cursor.location = cursor_orig_location

    # create Z trimmers
    z_pos_trimmer = create_z_pos_trimmer(bound_box, dimensions, buffer)
    z_pos_trimmer.name = 'Z Pos Trimmer.' + tile_name

    z_neg_trimmer = create_z_neg_trimmer(bound_box, dimensions, buffer)
    z_neg_trimmer.name = 'Z Neg Trimmer.' + tile_name

    cursor.location = cursor_orig_location
    z_trimmers = [z_pos_trimmer, z_neg_trimmer]

    if tile_props.degrees_of_arc >= 0:
        if tile_props.degrees_of_arc + 12.5 < 360:
            arc_adjusted = tile_props.degrees_of_arc + 12.5
        else:
            arc_adjusted = 359.999
    else:
        if tile_props.degrees_of_arc - 12.5 > -360:
            arc_adjusted = tile_props.degrees_of_arc - 12.5
        else:
            arc_adjusted = -359.999

    for trimmer in z_trimmers:
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')    
        add_deform_modifiers(trimmer, tile_props.segments, arc_adjusted)

    trimmers = [
        x_neg_trimmer,
        x_pos_trimmer,
        z_pos_trimmer,
        z_neg_trimmer
    ]

    cursor.location = cursor_orig_location

    save_trimmer_props(trimmers, tile_empty, tile_name)

    bpy.ops.object.delete({"selected_objects": [bbox_proxy]})

    return trimmers


def save_trimmer_props(trimmers, tile_empty, tile_name):
    ctx = {
        'selected_objects': trimmers,
        'active_object': trimmers[0],
        'object': trimmers[0]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    for trimmer in trimmers:
        trimmer.display_type = 'BOUNDS'

        trimmer.parent = tile_empty

        obj_props = trimmer.mt_object_props
        obj_props.tile_name = tile_name
        obj_props.geometry_type = 'TRIMMER'
        obj_props.is_mt_object = True

        # Store references to trimmers
        item = bpy.context.collection.mt_tile_props.trimmers_collection.add()
        item.name = trimmer.name
        item.value = False
        item.parent = tile_empty.name


def create_curved_floor_trimmers(tile_properties):
    mode('OBJECT')
    deselect_all

    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()

    scene = bpy.context.scene
    angle = tile_properties['angle']
    length = tile_properties['radius']

    dim = calc_tri(angle, length, length)
    dim['loc_A'] = cursor_orig_location
    dim['height'] = tile_properties['tile_height']

    buffer = bpy.context.scene.mt_trim_buffer

    a_trimmer = create_curved_trimmer(angle, length, dim['height'] + 1, 1, tile_properties['curve_type'], tile_props.segments, dim, buffer)
    a_trimmer.name = tile_name + '.a_trimmer'
    b_trimmer = create_b_trimmer(dim)
    b_trimmer.name = tile_name + '.b_trimmer'
    c_trimmer = create_c_trimmer(dim)
    c_trimmer.name = tile_name + '.c_trimmer'

    z_pos_trimmer = create_z_pos_tri_trimmer(dim)
    z_pos_trimmer.name = tile_name + '.z_pos_trimmer'
    z_neg_trimmer = create_z_neg_tri_trimmer(dim)
    z_neg_trimmer.name = tile_name + '.z_neg_trimmer'

    trimmers = {
        'x_neg': b_trimmer,
        'y_neg': c_trimmer,
        'x_pos': a_trimmer,
        'z_pos': z_pos_trimmer,
        'z_neg': z_neg_trimmer
    }

    for trimmer in trimmers.values():
        trimmer.display_type = 'BOUNDS'
        select(trimmer.name)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        trimmer.hide_viewport = True
        trimmer.parent = bpy.context.scene.objects[tile_properties['empty_name']]

    return trimmers


def create_curved_trimmer(arc, radius, height, width, curve_type, segments, dim, buffer):
    mode('OBJECT')
    deselect_all()

    if curve_type == 'POS':
        trimmer = draw_curved_slab(radius - buffer, arc, height, width, segments)
        t = bpy.ops.turtle
        t.select_all()
        t.dn(d=0.5, m=True)
        t.deselect_all()
        t.home()
        mode('OBJECT')
    else:
        t = bpy.ops.turtle
        turtle = bpy.context.scene.cursor
        t.add_turtle()
        t.pu()
        t.rt(d=arc)
        t.fd(d=radius)
        t.lt(d=180 - dim['C'] * 2)
        t.fd(d=radius)
        t.lt(d=180)
        t.arc(r=radius + buffer, d=arc, s=segments)
        t.arc(r=radius - width, d=arc, s=segments)
        t.select_all()
        t.bridge()
        t.select_all()
        t.pd()
        t.up(d=height + 1)
        t.select_all()
        t.dn(d=0.5, m=True)
        t.deselect_all()
        t.home()
        mode('OBJECT')

    return bpy.context.object


def create_corner_wall_tile_trimmers(tile_props, tile_empty):
    deselect_all()
    tile_name = tile_props.tile_name
    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()

    bbox_proxy = draw_cuboid([
        tile_props.leg_1_len,
        tile_props.leg_2_len,
        tile_props.tile_size[2]])

    mode('OBJECT')

    # get bounding box and dimensions of cuboid
    bound_box = bbox_proxy.bound_box
    dimensions = bbox_proxy.dimensions.copy()

    # create trimmers
    buffer = bpy.context.scene.mt_trim_buffer
    x_neg_trimmer = create_x_neg_trimmer(bound_box, dimensions, buffer)
    x_neg_trimmer.name = 'X Neg Trimmer.' + tile_name
    x_pos_trimmer = create_x_pos_trimmer(bound_box, dimensions, buffer)
    x_pos_trimmer.name = 'X Pos Trimmer.' + tile_name
    y_neg_trimmer = create_y_neg_trimmer(bound_box, dimensions, buffer)
    y_neg_trimmer.name = 'Y Neg Trimmer.' + tile_name
    y_pos_trimmer = create_y_pos_trimmer(bound_box, dimensions, buffer)
    y_pos_trimmer.name = 'Y Pos Trimmer.' + tile_name
    z_neg_trimmer = create_z_neg_trimmer(bound_box, dimensions, buffer)
    z_neg_trimmer.name = 'Z Neg Trimmer.' + tile_name
    z_pos_trimmer = create_z_pos_trimmer(bound_box, dimensions, buffer)
    z_pos_trimmer.name = 'Z Pos Trimmer.' + tile_name

    trimmers = [
        x_neg_trimmer,
        x_pos_trimmer,
        y_neg_trimmer,
        y_pos_trimmer,
        z_pos_trimmer,
        z_neg_trimmer
    ]

    cursor.location = cursor_orig_location

    save_trimmer_props(trimmers, tile_empty, tile_name)

    bpy.ops.object.delete({"selected_objects": [bbox_proxy]})
    return trimmers


def create_tri_floor_tile_trimmers(tile_properties, dim):
    mode('OBJECT')
    deselect_all()

    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()
    dim['height'] = tile_props.tile_size[2]
    b_trimmer = create_b_trimmer(dim)
    b_trimmer.name = tile_name + '.b_trimmer'
    c_trimmer = create_c_trimmer(dim)
    c_trimmer.name = tile_name + '.c_trimmer'
    a_trimmer = create_a_trimmer(dim)
    a_trimmer.name = tile_name + '.a_trimmer'
    z_pos_trimmer = create_z_pos_tri_trimmer(dim)
    z_pos_trimmer.name = tile_name + '.z_pos_trimmer'
    z_neg_trimmer = create_z_neg_tri_trimmer(dim)
    z_neg_trimmer.name = tile_name + '.z_neg_trimmer'

    trimmers = {
        'x_neg': b_trimmer,
        'y_neg': c_trimmer,
        'x_pos': a_trimmer,
        'z_pos': z_pos_trimmer,
        'z_neg': z_neg_trimmer
    }

    for trimmer in trimmers.values():
        trimmer.display_type = 'BOUNDS'
        select(trimmer.name)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        trimmer.hide_viewport = True
        trimmer.parent = bpy.context.scene.objects[tile_properties['empty_name']]

    return trimmers


def create_z_neg_tri_trimmer(dim):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    buffer = bpy.context.scene.mt_trim_buffer
    turtle.location = (
        dim['loc_A'][0] - 0.25,
        dim['loc_A'][1] - 0.25,
        dim['loc_A'][2] + buffer
    )
    t.add_turtle()
    t.pu()

    trimmer = bpy.context.object
    t.add_vert()
    t.pd()
    trimmer, dimensions = draw_tri_prism(dim['b'] + 1, dim['c'] + 1, dim['A'], -1)
    t.select_all()
    t.pu()
    t.home()
    mode('OBJECT')

    return trimmer


def create_z_pos_tri_trimmer(dim):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    buffer = bpy.context.scene.mt_trim_buffer
    turtle.location = (
        dim['loc_A'][0] - 0.25,
        dim['loc_A'][1] - 0.25,
        dim['loc_A'][2] + dim['height']
    )
    t.add_turtle()
    t.pu()

    trimmer = bpy.context.object
    t.add_vert()
    t.pd()
    trimmer, dimensions = draw_tri_prism(dim['b'] + 1, dim['c'] + 1, dim['A'], 1)
    t.select_all()
    t.pu()
    t.home()
    mode('OBJECT')

    return trimmer


def create_a_trimmer(dim):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    buffer = bpy.context.scene.mt_trim_buffer

    t.add_turtle()
    t.pu()

    trimmer = bpy.context.object

    # TODO: fix difference between loc_B and angle B
    t.setp(v=dim['loc_B'])
    t.rt(d=180 - dim['C'])
    t.ri(d=buffer)
    t.bk(d=0.5)
    t.dn(d=0.5)
    t.pd()
    t.add_vert()
    t.up(d=dim['height'] + 1)
    t.select_all()
    t.lf(d=1)
    t.select_all()
    t.fd(d=1 + dim['a'])
    t.pu()
    t.home()
    mode('OBJECT')

    return trimmer


def create_c_trimmer(dim):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    buffer = bpy.context.scene.mt_trim_buffer

    t.add_turtle()
    t.pu()

    trimmer = bpy.context.object

    t.setp(v=dim['loc_A'])
    t.rt(d=dim['A'])
    t.bk(d=0.5)
    t.lf(d=buffer)
    t.dn(d=0.5)
    t.pd()
    t.add_vert()
    t.up(d=dim['height'] + 1)
    t.select_all()
    t.fd(d=dim['c'] + 1)
    t.select_all()
    t.ri(d=1)
    t.pu()
    t.home()
    mode('OBJECT')

    return trimmer


def create_b_trimmer(dim):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    buffer = bpy.context.scene.mt_trim_buffer

    t.add_turtle()
    t.pu()

    trimmer = bpy.context.object

    t.setp(v=dim['loc_A'])
    t.bk(d=0.5)
    t.lf(d=buffer)
    t.dn(d=0.5)
    t.pd()
    t.add_vert()
    t.up(d=dim['height'] + 1)
    t.select_all()
    t.fd(d=dim['b'] + 1)
    t.select_all()
    t.lf(d=1)
    t.pu()
    t.home()
    mode('OBJECT')

    return trimmer


def add_bool_modifier(obj, trimmer_name):
    trimmer = bpy.data.objects[trimmer_name]
    boolean = obj.modifiers.new(trimmer.name + '.bool', 'BOOLEAN')
    boolean.show_viewport = False
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer


def trim_side(obj, trimmer_name):
    trimmer = bpy.data.objects[trimmer_name]
    boolean = obj.modifiers[trimmer.name + '.bool']
    boolean.show_viewport = True


def create_x_neg_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]

    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.ri(d=buffer)
    t.dn(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    t.lf(d=0.5)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object


def create_x_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_right = bound_box[4]

    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_right)))
    t.lf(d=buffer)
    t.dn(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    t.ri(d=0.5)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object


def create_y_neg_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.fd(d=buffer)
    t.lf(d=0.5)
    t.dn(d=0.5)
    t.pd()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.bk(d=0.5)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object


def create_y_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.fd(d=dimensions[1])
    t.bk(d=buffer)
    t.lf(d=0.5)
    t.dn(d=0.5)
    t.pd()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.fd(d=0.5)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object


def create_z_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_top_left = bound_box[2]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_top_left)))
    t.dn(d=buffer)
    t.lf(d=0.5)
    t.bk(d=1)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.up(d=0.5)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object


def create_z_neg_trimmer(bound_box, dimensions, buffer):

    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.up(d=buffer)
    t.lf(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.dn(d=0.5)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    mode('OBJECT')
    return bpy.context.object
