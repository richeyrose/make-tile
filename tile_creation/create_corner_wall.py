import os
import bpy
from math import tan, radians
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.vertex_groups import corner_wall_to_vert_groups
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs

from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials)

from . create_straight_wall_tile import create_openlock_wall_cutters

from .. operators.trim_tile import (
    create_corner_wall_tile_trimmers,
    add_bool_modifier)

from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)

from . create_displacement_mesh import create_displacement_object
from . generic import finalise_tile


def create_corner_wall(tile_empty):
    """Creates a corner wall tile
    Keyword arguments:
    tile_empty -- EMPTY, empty which the tile is parented to.
    """
    # hack to correct for parenting issues.
    # moves cursor to origin and creates objects
    # then moves base to cursor original location and resets cursor
    scene = bpy.context.scene
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    tile_empty.location = (0, 0, 0)

    tile_props = bpy.context.collection.mt_tile_props
    tile_name = tile_props.tile_name

    # Get base and main part blueprints
    base_blueprint = tile_props.base_blueprint
    main_part_blueprint = tile_props.main_part_blueprint

    # store some tile props
    tile_props.leg_1_len = scene.mt_leg_1_len
    tile_props.leg_2_len = scene.mt_leg_2_len
    tile_props.angle = scene.mt_angle

    # We store a list of meshes here because we're going to add
    # trimmer modifiers to all of them later but we don't yet
    # know the full dimensions of our tile
    tile_meshes = []
    if base_blueprint == 'OPENLOCK':
        tile_props.base_size = Vector((1, 0.5, 0.2755))
        base = create_openlock_base()
        tile_meshes.append(base)

    if base_blueprint == 'PLAIN':
        base, base_triangles, vert_locs = create_plain_base()
        tile_meshes.append(base)

    if base_blueprint == 'NONE':
        # If we have no base create an empty instead for storing details on
        # and parenting
        tile_props.base_size = (0, 0, 0)
        base = bpy.data.objects.new(tile_name + '.base', None)
        add_object_to_collection(base, tile_name)
        
    if tile_props.main_part_blueprint == 'OPENLOCK':
        tile_props.tile_size = Vector((
            scene.mt_tile_x,
            0.3149,
            scene.mt_tile_z))

        preview_core, displacement_core = create_openlock_cores(base)
        tile_meshes.extend([preview_core, displacement_core])

    if tile_props.main_part_blueprint == 'PLAIN':
        tile_props.tile_size = Vector((
            scene.mt_tile_x,
            scene.mt_tile_y,
            scene.mt_tile_z))
        preview_core, displacement_core = create_plain_cores(base)
        tile_meshes.extend([preview_core, displacement_core])

    if main_part_blueprint == 'NONE':
        tile_props.tile_size = tile_props.base_size

    trimmers = create_corner_wall_tile_trimmers(tile_props, tile_empty, base)

    finalise_tile(tile_meshes,
                  trimmers,
                  tile_empty,
                  base,
                  preview_core,
                  cursor_orig_loc)


def create_plain_base():

    tile_props = bpy.context.collection.mt_tile_props

    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    base_height = tile_props.base_size[2]
    angle = tile_props.angle
    base_thickness = tile_props.base_size[1]

    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()

    base_triangles = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        base_thickness,
        angle)

    vert_locs = draw_corner_outline(base_triangles, angle, base_thickness)
    t.select_all()
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    t.pu()
    t.deselect_all()
    t.home()
    bpy.ops.object.editmode_toggle()
    base = bpy.context.object

    return base, base_triangles, vert_locs


def create_openlock_base():
    tile_props = bpy.context.collection.mt_tile_props

    base, base_triangles, vert_locs = create_plain_base()

    slot_cutter = create_openlock_base_slot_cutter()

    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'
    slot_cutter.hide_viewport = True

    # clip cutters - leg 1
    leg_len = base_triangles['b_adj']
    corner_loc = vert_locs['d']
    clip_cutter_1 = create_openlock_base_clip_cutter(leg_len, corner_loc, -0.25)
    select(clip_cutter_1.name)
    bpy.ops.transform.mirror(constraint_axis=(False, True, False))
    bpy.ops.transform.rotate(
        value=radians(tile_props.angle - 90),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=corner_loc)

    # clip cutters - leg 2
    leg_len = base_triangles['d_adj']
    corner_loc = vert_locs['d']
    clip_cutter_2 = create_openlock_base_clip_cutter(leg_len, corner_loc, 0.25)
    select(clip_cutter_2.name)
    bpy.ops.transform.rotate(
        value=radians(-90),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=corner_loc)

    cutters = [clip_cutter_1, clip_cutter_2]
    for cutter in cutters:
        cutter_boolean = base.modifiers.new(cutter.name, 'BOOLEAN')
        cutter_boolean.operation = 'DIFFERENCE'
        cutter_boolean.object = cutter
        cutter.parent = base
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True

    deselect_all()

    return base


def create_openlock_base_clip_cutter(leg_len, corner_loc, offset):
    tile_props = bpy.context.collection.mt_tile_props
    mode('OBJECT')
    # load cutter
    # Get cutter
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

    # load base cutters
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_props.tile_name)

    clip_cutter = data_to.objects[0]
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    cutter_start_cap.hide_viewport = True
    cutter_end_cap.hide_viewport = True

    clip_cutter.location = Vector((
        corner_loc[0] + 0.5,
        corner_loc[1] + offset,
        corner_loc[2]
    ))

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = leg_len - 1

    return clip_cutter


def create_openlock_cores(base):
    tile_props = bpy.context.collection.mt_tile_props
    cursor = bpy.context.scene.cursor
    preview_core, displacement_core = create_plain_cores(base)

    cores = [preview_core, displacement_core]

    cutters = create_openlock_wall_cutters(preview_core)
    left_cutters = [cutters[0], cutters[1]]
    right_cutters = [cutters[2], cutters[3]]

    deselect_all()

    for cutter in right_cutters:
        cutter.location = (
            cutter.location[0] + tile_props.leg_1_len - 1,
            cutter.location[1] + (tile_props.base_size[1] / 2),
            cutter.location[2])
        select(cutter.name)
    bpy.ops.transform.rotate(
        value=radians(tile_props.angle - 90),
        orient_axis='Z',
        center_override=cursor.location)

    deselect_all()

    for cutter in left_cutters:
        cutter.location = (
            cutter.location[0] - tile_props.leg_2_len + 1,
            cutter.location[1] + (tile_props.base_size[1] / 2),
            cutter.location[2])
        select(cutter.name)
    bpy.ops.transform.rotate(
        value=-radians(-90),
        orient_axis='Z',
        center_override=cursor.location)

    deselect_all()

    for cutter in cutters:
        cutter.parent = base
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True
        obj_props = cutter.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        obj_props.geometry_type = 'CUTTER'

        for core in cores:
            cutter_bool = core.modifiers.new(cutter.name + '.bool', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = cutter

            # add cutters to object's mt_cutters_collection
            # so we can activate and deactivate them when necessary
            item = core.mt_object_props.cutters_collection.add()
            item.name = cutter.name
            item.value = True
            item.parent = core.name

    return preview_core, displacement_core


def create_plain_cores(base):
    tile_props = bpy.context.collection.mt_tile_props

    preview_core = create_plain_wall_core()
    preview_core, displacement_core = create_displacement_object(preview_core)

    preview_core.parent = base
    displacement_core.parent = base

    preferences = get_prefs()

    primary_material = bpy.data.materials[bpy.context.scene.mt_tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_tile_resolution

    assign_displacement_materials(displacement_core, [image_size, image_size], primary_material, secondary_material)
    assign_preview_materials(preview_core, primary_material, secondary_material, textured_vertex_groups=['Outer', 'Inner', 'Top'])

    displacement_core.hide_viewport = True

    return preview_core, displacement_core


def create_openlock_base_slot_cutter():
    tile_props = bpy.context.collection.mt_tile_props
    base_thickness = tile_props.base_size[1]
    wall_thickness = tile_props.tile_size[1]
    base_height = tile_props.base_size[2]
    wall_height = tile_props.tile_size[2]
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle

    if bpy.context.scene.mt_base_socket_side == 'INNER':
        face_dist = 0.07
    else:
        face_dist = 0.233  # distance from outer face our slot should start

    slot_width = 0.197
    slot_height = 0.25
    end_dist = 0.236  # distance of slot from base end

    cutter_triangles_1 = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        face_dist,
        angle)

    # reuse method we use to work out where to start our wall
    move_cursor_to_wall_start(
        cutter_triangles_1,
        angle,
        face_dist,
        -0.01)

    cutter_x_leg = cutter_triangles_1['b_adj'] - end_dist
    cutter_y_leg = cutter_triangles_1['d_adj'] - end_dist

    # work out dimensions of cutter
    cutter_triangles_2 = calculate_corner_wall_triangles(
        cutter_x_leg,
        cutter_y_leg,
        slot_width,
        angle
    )

    draw_corner_outline(
        cutter_triangles_2,
        angle,
        slot_width
    )

    # fill face and extrude cutter
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=slot_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    t.pu()
    t.deselect_all()
    t.home()

    mode('OBJECT')
    cutter = bpy.context.object
    cutter.name = tile_props.tile_name + '.base.cutter'

    return cutter


def calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle):
    # X leg
    # right triangle
    tri_a_angle = angle / 2
    tri_a_adj = leg_1_len
    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    # right triangle
    tri_b_angle = 180 - tri_a_angle - 90
    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))

    # Y leg
    # right triangle
    tri_c_angle = angle / 2
    tri_c_adj = leg_2_len
    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_angle = 180 - tri_c_angle - 90
    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,  # leg 1 outer leg length
        'b_adj': tri_b_adj,  # leg 1 inner leg length
        'c_adj': tri_c_adj,  # leg 2 outer leg length
        'd_adj': tri_d_adj}  # leg 2 inner leg length

    return triangles


def move_cursor_to_wall_start(triangles, angle, thickness, base_height):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
    orig_rot = turtle.rotation_euler.copy()
    t.pu()
    t.up(d=base_height, m=True)
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    t.lt(d=90)
    t.fd(d=thickness)
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    turtle.rotation_euler = orig_rot


def draw_corner_outline(triangles, angle, thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    orig_loc = turtle.location.copy()
    orig_rot = turtle.rotation_euler.copy()

    # We save the location of each vertex as it is drawn
    # to use for making vert groups & positioning cutters
    vert_loc = {
        'a': orig_loc
    }
    t.pd()
    # draw X leg
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    vert_loc['b'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=thickness)
    vert_loc['c'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    vert_loc['d'] = turtle.location.copy()

    # home
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    t.deselect_all()
    t.select_at_cursor()
    t.pd()  # vert loc same as a

    # draw Y leg
    t.fd(d=triangles['c_adj'])
    vert_loc['e'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=thickness)
    vert_loc['f'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=triangles['d_adj'])  # vert loc same as d

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    return vert_loc


def create_plain_wall_core():
    tile_props = bpy.context.collection.mt_tile_props

    base_thickness = tile_props.base_size[1]
    wall_thickness = tile_props.tile_size[1]
    base_height = tile_props.base_size[2]
    wall_height = tile_props.tile_size[2]
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle

    thickness_diff = base_thickness - wall_thickness

    # first work out where we're going to start drawing our wall
    # from, taking into account the difference in thickness
    # between the base and wall and how long our legs will be
    core_triangles_1 = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness_diff / 2,
        angle)

    move_cursor_to_wall_start(
        core_triangles_1,
        angle,
        thickness_diff / 2,
        base_height)

    core_x_leg = core_triangles_1['b_adj']
    core_y_leg = core_triangles_1['d_adj']

    # work out dimensions of core
    core_triangles_2 = calculate_corner_wall_triangles(
        core_x_leg,
        core_y_leg,
        wall_thickness,
        angle)

    # store the vertex locations for turning
    # into vert groups as we draw outline
    vert_locs = draw_corner_outline(
        core_triangles_2,
        angle,
        wall_thickness)

    # fill face and extrude wall
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    bpy.ops.mesh.edge_face_add()
    t.pd()
    t.up(d=wall_height - base_height)
    t.select_all()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.uv.smart_project(island_margin=1)
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    t.pu()
    t.deselect_all()
    t.home()

    # create vert groups
    corner_wall_to_vert_groups(bpy.context.object, vert_locs)

    mode('OBJECT')
    core = bpy.context.object
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core
