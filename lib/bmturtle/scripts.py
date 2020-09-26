from math import cos, acos, sqrt, degrees, radians
from mathutils import kdtree
import bmesh
import bpy
from .commands import (
    create_turtle,
    finalise_turtle,
    add_vert,
    fd,
    ri,
    up,
    dn,
    pu,
    pd,
    home,
    arc,
    rt,
    lt)
from .helpers import (
    bm_select_all,
    bm_deselect_all,
    assign_verts_to_group,
    select_verts_in_bounds,
    bm_shortest_path)

def draw_cuboid(dimensions):
    """Draw a cuboid.

    Args:
        dimensions (Vactor[3]): dimensions

    Returns:
        obj: bpy.types.Object
    """
    bm, obj = create_turtle(name='cuboid')
    add_vert(bm)
    bm.select_mode = {'VERT'}
    fd(bm, dimensions[1])
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    ri(bm, dimensions[0])
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, dimensions[2], False)
    pu(bm)

    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_tri_prism(dimensions, ret_dimensions=False):
    """Draws a triangular prism

    Args:
        dimensions (dict{b, c, A, height}): dimensions
        ret_dimensions (bool): return calculated dimensions

    Returns:
        bpy.types.Object: triangular prism
        dict: dimensions{a, b, c, A, B, C, loc_A, loc_B, loc_C}
    """

    #      B
    #      /\
    #   c /  \ a
    #    /    \
    #   /______\
    #  A    b    C

    b = dimensions['b']
    c = dimensions['c']
    A = dimensions['A']
    height = dimensions['height']

    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    turtle = bpy.context.scene.cursor

    bm, obj = create_turtle(name='tri_prism')
    add_vert(bm)
    bm.select_mode = {'VERT'}
    loc_A = turtle.location.copy()
    fd(bm, c)
    loc_B = turtle.location.copy()
    rt(180 - B)
    fd(bm, a)
    loc_C = turtle.location.copy()
    bmesh.ops.contextual_create(
        bm,
        geom=bm.verts,
        mat_nr=0,
        use_smooth=False)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)
    home(obj)
    finalise_turtle(bm, obj)

    dimensions = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C,
        'loc_A': loc_A,
        'loc_B': loc_B,
        'loc_C': loc_C}

    if ret_dimensions:
        return obj, dimensions

    return obj


def draw_tri_floor_core(dimensions, subdivs, margin=0.001):
    """Draw a triangular floor core and create vertex groups

    Args:
        dimensions (dict{a, c, A, height}): dimensions
        subdivs (list): subdivs(edge, height)
        margin (float, optional): margin. Defaults to 0.001.

    Returns:
        bpy.types.Object: core
    """
    #      B
    #      /\
    #   c /  \ a
    #    /    \
    #   /______\
    #  A    b    C
    subdivs[0] = 15
    b = dimensions['b']
    c = dimensions['c']
    A = dimensions['A']
    height = dimensions['height']

    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    turtle = bpy.context.scene.cursor

    vert_groups = ['Side a', 'Side b', 'Side c', 'Top', 'Bottom']

    bm, obj = create_turtle(name='tri_prism', vert_groups=vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active

    # draw bottom
    add_vert(bm)
    bm.select_mode = {'VERT'}
    loc_A = turtle.location.copy()
    fd(bm, c)
    loc_B = turtle.location.copy()
    rt(180 - B)
    fd(bm, a)
    loc_C = turtle.location.copy()

    bmesh.ops.contextual_create(
        bm,
        geom=bm.verts,
        mat_nr=0,
        use_smooth=False)

    bmesh.ops.subdivide_edges(
        bm,
        edges=bm.edges,
        cuts=subdivs[0],
        use_grid_fill=True)

    bottom_verts = [v for v in bm.verts]

    bm.select_mode = {'FACE'}
    faces = [f for f in bm.faces]
    for f in faces:
        f.select_set(True)

    for i in range(subdivs[1]):
        up(bm, height / subdivs[1], False)

    faces = [f for f in bm.faces if f.select]
    bm.select_mode = {'VERT'}
    bmesh.ops.inset_region(bm, faces=faces, thickness=margin)
    bm_deselect_all(bm)

    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')
    bm_deselect_all(bm)

    buffer = margin / 2

    # select side c and assign to vert group
    lbound = loc_A
    ubound = (
        loc_B[0],
        loc_B[1],
        loc_B[2] + height)

    side_c_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(side_c_verts, obj, deform_groups, 'Side c')
    bm_deselect_all(bm)

    # select side a and assign to vert group
    side_a_verts = []
    pu(bm)
    turtle.location = loc_A
    turtle.rotation_euler = (0, 0, 0)

    fd(bm, c)
    rt(180 - B)

    i = 0
    while i <= subdivs[0]:
        lbound = turtle.location
        ubound = (
            turtle.location[0],
            turtle.location[1],
            turtle.location[2] + height)
        selected_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
        side_a_verts.extend(selected_verts)
        fd(bm, a / (subdivs[0] + 1))
        i += 1
    lbound = turtle.location
    ubound = (
        turtle.location[0],
        turtle.location[1],
        turtle.location[2] + height)
    selected_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    side_a_verts.extend(selected_verts)

    assign_verts_to_group(side_a_verts, obj, deform_groups, 'Side a')
    bm_deselect_all(bm)

    # select side b and assign verts
    side_b_verts = []
    rt(180 - C)

    i = 0
    while i <= subdivs[0]:
        lbound = turtle.location
        ubound = (
            turtle.location[0],
            turtle.location[1],
            turtle.location[2] + height)
        selected_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
        side_b_verts.extend(selected_verts)
        fd(bm, b / (subdivs[0] + 1))
        i += 1
    lbound = turtle.location
    ubound = (
        turtle.location[0],
        turtle.location[1],
        turtle.location[2] + height)
    selected_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    side_b_verts.extend(selected_verts)

    assign_verts_to_group(side_b_verts, obj, deform_groups, 'Side b')

    bm_deselect_all(bm)

    # select top and assign verts
    top_verts = []
    lbound = (
        loc_A[0],
        loc_A[1],
        loc_A[2] + height)
    ubound = (
        loc_C[0] + b,
        loc_B[1],
        loc_A[2] + height)

    side_verts = side_a_verts + side_b_verts + side_c_verts
    selected_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    top_verts = [v for v in selected_verts if v not in side_verts]

    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_tri_slot_cutter(dimensions):
    """Return a triangle floor cutter.

    Args:
        dimensions (dict{b, c, A}): Base dimensions

    Returns:
        bpy.types.Object: slot cutter
    """
    #      B
    #      /\
    #   c /  \ a
    #    /    \
    #   /______\
    #  A    b    C

    # dimensions
    offset = 0.24     # distance from edge for slot
    cutter_w = 0.185
    cutter_h = 0.24

    b = dimensions['b']
    c = dimensions['c']
    A = dimensions['A']

    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))

    bm, obj = create_turtle(name='Slot.')

    dn(bm, 0.001)

    add_vert(bm)
    bm.select_mode = {'VERT'}

    # draw outer loop
    fd(bm, c)
    rt(180 - B)
    fd(bm, a)
    bm.faces.ensure_lookup_table()
    bmesh.ops.contextual_create(
        bm,
        geom=bm.verts,
        mat_nr=0,
        use_smooth=False)

    # inset to get slot

    ret = bmesh.ops.inset_individual(bm, faces=bm.faces, thickness=offset, use_even_offset=True)

    # delete other faces
    to_delete = []
    for f in bm.faces:
        if f in ret['faces']:
            to_delete.append(f)

    bmesh.ops.delete(bm, geom=to_delete, context='FACES')

    ret2 = bmesh.ops.inset_individual(bm, faces=bm.faces, thickness=cutter_w, use_even_offset=True)

    # delete other faces
    to_delete = []
    for f in bm.faces:
        if f not in ret2['faces']:
            to_delete.append(f)

    bmesh.ops.delete(bm, geom=to_delete, context='FACES')

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, cutter_h, False)

    home(obj)
    finalise_turtle(bm, obj)
    return obj


def draw_straight_wall_core(dims, subdivs, margin=0.001):
    """Draws a Straight Wall Core and assigns Verts to appropriate groups

    Args:
        dims (tuple[3]): Dimensions
        subdivs (tuple[3]): How many times to subdivide each face
        margin (float, optional): Margin to leave around textured areas to correct for displacement distortion.
        Defaults to 0.001.

    Returns:
        bpy.types.Object: Wall Core
    """
    vert_groups = ['Left', 'Right', 'Front', 'Back', 'Top', 'Bottom']

    bm, obj = create_turtle('Straight Wall', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    bottom_verts = []
    top_verts = []

    # Start drawing wall
    pd(bm)
    add_vert(bm)
    bm.select_mode = {'VERT'}

    # Draw front bottom edges
    ri(bm, margin)

    subdiv_x_dist = (dims[0] - (margin * 2)) / subdivs[0]

    i = 0
    while i < subdivs[0]:
        ri(bm, subdiv_x_dist)
        i += 1

    ri(bm, margin)

    # Select edge and extrude to create bottom
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    fd(bm, margin)

    subdiv_y_dist = (dims[1] - (margin * 2)) / subdivs[1]

    i = 0
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist)
        i += 1

    fd(bm, margin)

    # Save verts to add to bottom vert group
    for v in bm.verts:
        bottom_verts.append(v)

    # select bottom and extrude up
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, margin, False)

    subdiv_z_dist = (dims[2] - (margin * 2)) / subdivs[2]

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    up(bm, margin)

    # Save top verts to add to top vertex group
    top_verts = [v for v in bm.verts if v.select]

    # assign bottom verts to vertex groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')

    # home turtle
    pu(bm)

    home(obj)

    # select left side and assign to vert group
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)
    left_verts = [v for v in left_verts_orig if v not in top_verts]
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')

    # select right side and assign to vert group
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)
    right_verts = [v for v in right_verts_orig if v not in top_verts]
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')

    # make sure top verts doesn;t contain any verts from ends
    top_verts = [v for v in top_verts if v not in left_verts_orig and v not in right_verts_orig]
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')

    # select front side and assign to vert group
    lbound = (margin, 0, margin)
    ubound = (dims[0] - margin, 0, dims[2] - margin)
    buffer = margin / 2

    front_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')

    # select back side and assign to vert group
    lbound = (margin, dims[1], margin)
    ubound = (dims[0] - margin, dims[1], dims[2] - margin)
    buffer = margin / 2

    back_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def draw_corner_core(
        dimensions,
        native_subdivisions,
        margin=0.001):
    """Draw a corner core.

    Args:
        dimensions (dict {
            triangles_1: dict,
            triangles_2: dict,
            angle: float,
            thickness: float,
            thickness_diff: float,
            base_height: float,
            height: float}): dimensions
        native_subdivisions (dict {
            leg 1: int,
            leg 2: int,
            width: int,
            height: int }): subdivisions
        margin (float, optional): margin for texture. Defaults to 0.001.

    Returns:
        bmesh: bmesh
        bpy.types.Object: core object
        bm.verts.layers.deform: deform groups - corresponds to vertex groups
        dict {
            'Leg 1 Inner': list[Vector(3)],
            'Leg 2 Inner': list[Vector(3)],
            'Leg 1 Outer': list[Vector(3)],
            'Leg 2 Outer': list[Vector(3)],
            'Leg 1 End': list[Vector(3)],
            'Leg 2 End': list[Vector(3)]} : Locations of bottom verts in each group
    """
    triangles_1 = dimensions['triangles_1']
    triangles_2 = dimensions['triangles_2']
    angle = dimensions['angle']
    thickness = dimensions['thickness']
    thickness_diff = dimensions['thickness_diff']
    base_height = dimensions['base_height']
    height = dimensions['height']

    turtle = bpy.context.scene.cursor
    turtle_start_loc = turtle.location.copy()
    vert_groups = [
        'Leg 1 End',
        'Leg 2 End',
        'Leg 1 Inner',
        'Leg 2 Inner',
        'Leg 1 Outer',
        'Leg 2 Outer',
        'Leg 1 Top',
        'Leg 2 Top',
        'Leg 1 Bottom',
        'Leg 2 Bottom']

    bm, obj = create_turtle('L_2D', vert_groups)
    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active

    bm.select_mode = {'VERT'}
    verts = bm.verts
    leg_1_end_vert_locs = []
    leg_1_inner_vert_locs = []
    leg_1_outer_vert_locs = []

    # move turtle to core start loc
    orig_rot = turtle.rotation_euler.copy()
    pu(bm)
    up(bm, base_height)
    rt(angle)
    fd(bm, triangles_1['a_adj'])
    lt(90)
    fd(bm, thickness_diff / 2)
    lt(90)
    fd(bm, triangles_1['b_adj'])
    turtle.rotation_euler = orig_rot
    turtle_start_loc = turtle.location.copy()
    pd(bm)
    # draw leg 1
    # outer edge
    subdiv_dist = (triangles_2['a_adj'] - margin) / native_subdivisions['leg 1']

    add_vert(bm)
    rt(angle)
    bm.verts.ensure_lookup_table()
    leg_1_outer_vert_locs.append(verts[-1].co.copy())

    i = 0
    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    while i < native_subdivisions['leg 1']:
        fd(bm, subdiv_dist)
        i += 1
    fd(bm, margin)

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_1_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    bm.verts.ensure_lookup_table()
    leg_1_end_vert_locs.append(verts[-1].co.copy())

    # end
    # we're going to bridge between inner and outer side
    # so we don't draw end edge
    pu(bm)
    lt(90)
    fd(bm, thickness)
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_1_end_vert_locs.append(verts[-1].co.copy())
    lt(90)

    # inner
    subdiv_dist = (triangles_2['b_adj'] - margin) / native_subdivisions['leg 1']
    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    fd(bm, margin)
    i = 0
    while i < native_subdivisions['leg 1']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_1_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    # home
    pu(bm)
    home(obj)
    turtle.location = turtle_start_loc
    pd(bm)

    # draw leg 2 #
    leg_2_outer_vert_locs = []
    leg_2_end_vert_locs = []
    leg_2_inner_vert_locs = []
    subdiv_dist = (triangles_2['c_adj'] - margin) / native_subdivisions['leg 2']

    # outer
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_2_outer_vert_locs.append(verts[-1].co.copy())
    start_index = verts[-1].index

    i = 0
    while i < native_subdivisions['leg 2']:
        fd(bm, subdiv_dist)
        i += 1
    fd(bm, margin)

    bm.verts.ensure_lookup_table()
    i = start_index + 1
    while i <= verts[-1].index:
        leg_2_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    # end
    pu(bm)
    rt(90)

    bm.verts.ensure_lookup_table()
    leg_2_end_vert_locs.append(verts[-1].co.copy())
    fd(bm, thickness)
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_2_end_vert_locs.append(verts[-1].co.copy())
    rt(90)

    # inner
    subdiv_dist = (triangles_2['d_adj'] - margin) / native_subdivisions['leg 2']
    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    fd(bm, margin)
    i = 0
    while i < native_subdivisions['leg 2']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_2_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    # bridge edge loops
    ret = bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bmesh.ops.subdivide_edges(bm, edges=ret['edges'], smooth=1, smooth_falloff='LINEAR', cuts=native_subdivisions['width'])

    # inset
    bmesh.ops.inset_region(bm, faces=bm.faces, use_even_offset=True, thickness=margin, use_boundary=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    # Z
    subdiv_dist = (height - (margin * 2)) / native_subdivisions['height']
    bm_select_all(bm)
    bm.select_mode = {'FACE'}

    up(bm, margin, False)

    i = 0
    while i < native_subdivisions['height']:
        up(bm, subdiv_dist)
        i += 1
    up(bm, margin)

    home(obj)

    vert_locs = {
        'Leg 1 Inner': leg_1_inner_vert_locs,
        'Leg 2 Inner': leg_2_inner_vert_locs,
        'Leg 1 Outer': leg_1_outer_vert_locs,
        'Leg 2 Outer': leg_2_outer_vert_locs,
        'Leg 1 End': leg_1_end_vert_locs,
        'Leg 2 End': leg_2_end_vert_locs}

    return bm, obj, deform_groups, vert_locs


def draw_corner_floor_core(
        dimensions,
        native_subdivisions,
        margin=0.001):
    """Draw a corner floor and assign verts to vertex groups.

    Args:
        dimensions (dict {
            triangles_1: dict,
            triangles_2: dict,
            angle: float,
            thickness: float,
            thickness_diff: float,
            base_height: float,
            height: float}): dimensions
        native_subdivisions (dict {
            leg 1: int,
            leg 2: int,
            width: int,
            height: int }): subdivisions
        margin (float, optional): margin for texture. Defaults to 0.001.

    Returns:
        bpy.types.Object: floor core
    """

    bm, core, deform_groups, vert_locs = draw_corner_core(
        dimensions,
        native_subdivisions,
        margin)

    vert_groups = create_corner_vert_groups_vert_lists(
        bm,
        dimensions['height'],
        margin,
        vert_locs)

    blank_groups = [
        'Leg 1 Inner',
        'Leg 1 Outer',
        'Leg 2 Inner',
        'Leg 2 Outer',
        'Leg 1 End',
        'Leg 2 End',
        'Leg 1 Bottom',
        'Leg 2 Bottom']

    blank_group_verts = set()

    for key, value in vert_groups.items():
        if key in blank_groups:
            blank_group_verts = blank_group_verts.union(value)

    top_groups = ['Leg 1 Top', 'Leg 2 Top']
    for group in top_groups:
        verts = [v for v in vert_groups[group] if v not in blank_group_verts]
        assign_verts_to_group(verts, core, deform_groups, group)

    for group in blank_groups:
        assign_verts_to_group(vert_groups[group], core, deform_groups, group)

    finalise_turtle(bm, core)

    return core


def draw_corner_wall_core(
        dimensions,
        native_subdivisions,
        margin=0.001):
    """Draw a corner wall core and assign verts to vertex groups.

    Args:
        dimensions (dict {
            triangles_1: dict,
            triangles_2: dict,
            angle: float,
            thickness: float,
            thickness_diff: float,
            base_height: float,
            height: float}): dimensions
        native_subdivisions (dict {
            leg 1: int,
            leg 2: int,
            width: int,
            height: int }): subdivisions
        margin (float, optional): margin for texture. Defaults to 0.001.

    Returns:
        bpy.types.Object: wall core
    """
    bm, core, deform_groups, vert_locs = draw_corner_core(
        dimensions,
        native_subdivisions,
        margin)

    vert_groups = create_corner_vert_groups_vert_lists(
        bm,
        dimensions['height'],
        margin,
        vert_locs)

    blank_groups = [
        'Leg 1 Top',
        'Leg 2 Top',
        'Leg 1 End',
        'Leg 2 End',
        'Leg 1 Bottom',
        'Leg 2 Bottom']

    textured_groups = [
        'Leg 1 Inner',
        'Leg 2 Inner',
        'Leg 1 Outer',
        'Leg 2 Outer']

    blank_group_verts = set()

    for key, value in vert_groups.items():
        if key in blank_groups:
            blank_group_verts = blank_group_verts.union(value)

    for group in textured_groups:
        verts = [v for v in vert_groups[group] if v not in blank_group_verts]
        assign_verts_to_group(verts, core, deform_groups, group)

    leg_1_end = [v for v in vert_groups['Leg 1 End'] if v not in vert_groups['Leg 1 Top']]
    assign_verts_to_group(leg_1_end, core, deform_groups, 'Leg 1 End')
    leg_2_end = [v for v in vert_groups['Leg 2 End'] if v not in vert_groups['Leg 2 Top']]
    assign_verts_to_group(leg_2_end, core, deform_groups, 'Leg 2 End')
    leg_1_top_verts = [v for v in vert_groups['Leg 1 Top'] if v not in vert_groups['Leg 1 End']]
    assign_verts_to_group(leg_1_top_verts, core, deform_groups, 'Leg 1 Top')
    leg_2_top_verts = [v for v in vert_groups['Leg 2 Top'] if v not in vert_groups['Leg 2 End']]
    assign_verts_to_group(leg_2_top_verts, core, deform_groups, 'Leg 2 Top')
    leg_1_bottom_verts = [v for v in vert_groups['Leg 1 Bottom'] if v not in vert_groups['Leg 1 End']]
    assign_verts_to_group(leg_1_bottom_verts, core, deform_groups, 'Leg 1 Bottom')
    leg_2_bottom_verts = [v for v in vert_groups['Leg 2 Bottom'] if v not in vert_groups['Leg 2 End']]
    assign_verts_to_group(leg_2_bottom_verts, core, deform_groups, 'Leg 2 Bottom')

    finalise_turtle(bm, core)

    return core


def create_corner_vert_groups_vert_lists(bm, height, margin, vert_locs):
    """Return a dict containing lists of BMVerts to be added to vert groups

    Args:
        bm (bmesh): bmesh
        obj (bpy.types.Object): Object
        height (float): height
        margin (float): margin size of untextured bit
        deform_groups (bm.verts.layers.deform): deform groups - correspond to vertex groups
        dict {
            'Leg 1 Inner': list[Vector(3)],
            'Leg 2 Inner': list[Vector(3)],
            'Leg 1 Outer': list[Vector(3)],
            'Leg 2 Outer': list[Vector(3)],
            'Leg 1 End': list[Vector(3)],
            'Leg 2 End': list[Vector(3)]} : Locations of bottom verts in each group

    Returns:
        dict {
            'Leg 1 Inner': list[BMVert],
            'Leg 2 Inner': list[BMVert],
            'Leg 1 Outer': list[BMVert],
            'Leg 2 Outer': list[BMVert],
            'Leg 1 End': list[BMVert],
            'Leg 2 End': list[BMVert]} : verts in each group
    """
    # sides
    sides = {
        'Leg 1 Inner': vert_locs['Leg 1 Inner'],
        'Leg 2 Inner': vert_locs['Leg 2 Inner'],
        'Leg 1 Outer': vert_locs['Leg 1 Outer'],
        'Leg 2 Outer': vert_locs['Leg 2 Outer']}
    vert_groups = {}

    # create kdtree
    size = len(bm.verts)
    kd = kdtree.KDTree(size)

    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)

    kd.balance()

    for key, value in sides.items():
        vert_group = []
        for loc in value:
            bottom_vert_co, index, dist = kd.find(loc)
            verts = select_verts_in_bounds(
                lbound=bottom_vert_co,
                ubound=(bottom_vert_co[0], bottom_vert_co[1], bottom_vert_co[2] + height),
                buffer=margin / 2,
                bm=bm)
            vert_group.extend(verts)
        vert_groups[key] = vert_group

        bm_deselect_all(bm)

    # ends
    ends = {
        'Leg 1 End': vert_locs['Leg 1 End'],
        'Leg 2 End': vert_locs['Leg 2 End']}

    for key, value in ends.items():
        v1_co, v1_index, dist = kd.find(value[0])
        v2_co, v2_index, dist = kd.find(value[1])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        # select shortest path
        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts = []

        for v in verts:
            selected = select_verts_in_bounds(v.co, (v.co[0], v.co[1], v.co[2] + height), margin / 2, bm)
            selected_verts.extend(selected)

        vert_groups[key] = selected_verts
        bm_deselect_all(bm)

    # bottom
    # leg 1
    inner_locs = vert_locs['Leg 1 Inner'][::-1]
    outer_locs = vert_locs['Leg 1 Outer']

    selected_verts = []
    i = 0
    while i < len(outer_locs) and i < len(inner_locs):
        v1_co, v1_index, dist = kd.find(inner_locs[i])
        v2_co, v2_index, dist = kd.find(outer_locs[i])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts.extend(verts)
        i += 1

    vert_groups['Leg 1 Bottom'] = selected_verts
    bm_deselect_all(bm)

    # leg 2
    inner_locs = vert_locs['Leg 2 Inner'][::-1]
    outer_locs = vert_locs['Leg 2 Outer']

    selected_verts = []
    i = 0
    while i < len(inner_locs) and i < len(outer_locs):
        v1_co, v1_index, dist = kd.find(inner_locs[i])
        v2_co, v2_index, dist = kd.find(outer_locs[i])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts.extend(verts)
        i += 1
    vert_groups['Leg 2 Bottom'] = selected_verts
    # assign_verts_to_group(selected_verts, obj, deform_groups, 'Leg 2 Bottom')

    # top
    # leg 1
    inner_locs = vert_locs['Leg 1 Inner'][::-1]
    outer_locs = vert_locs['Leg 1 Outer']

    leg_1_top_verts = []
    i = 0
    while i < len(inner_locs) and i < len(outer_locs):
        v1 = select_verts_in_bounds(
            (inner_locs[i][0],
             inner_locs[i][1],
             inner_locs[i][2] + height),
            (inner_locs[i][0],
             inner_locs[i][1],
             inner_locs[i][2] + height),
            margin / 2,
            bm)
        v2 = select_verts_in_bounds(
            (outer_locs[i][0],
             outer_locs[i][1],
             outer_locs[i][2] + height),
            (outer_locs[i][0],
             outer_locs[i][1],
             outer_locs[i][2] + height),
            margin / 2,
            bm)

        nodes = bm_shortest_path(bm, v1[0], v2[0])
        node = nodes[v2[0]]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        leg_1_top_verts.extend(verts)
        i += 1
    vert_groups['Leg 1 Top'] = leg_1_top_verts
    bm_deselect_all(bm)

    # leg 2
    inner_locs = vert_locs['Leg 2 Inner'][::-1]
    outer_locs = vert_locs['Leg 2 Outer']

    leg_2_top_verts = []
    i = 0
    while i < len(inner_locs) and i < len(outer_locs):
        v1 = select_verts_in_bounds(
            (inner_locs[i][0],
             inner_locs[i][1],
             inner_locs[i][2] + height),
            (inner_locs[i][0],
             inner_locs[i][1],
             inner_locs[i][2] + height),
            margin / 2,
            bm)
        v2 = select_verts_in_bounds(
            (outer_locs[i][0],
             outer_locs[i][1],
             outer_locs[i][2] + height),
            (outer_locs[i][0],
             outer_locs[i][1],
             outer_locs[i][2] + height),
            margin / 2,
            bm)

        nodes = bm_shortest_path(bm, v1[0], v2[0])
        node = nodes[v2[0]]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        leg_2_top_verts.extend(verts)
        i += 1
    vert_groups['Leg 2 Top'] = leg_2_top_verts
    bm_deselect_all(bm)

    return vert_groups


def draw_corner_slot_cutter(dimensions):
    """Draw a slot cutter for an openlock corner base.

    Args:
        triangles (dict {
            'a_adj': float, (leg 1 outer leg length)
            'b_adj': float, (leg 1 inner leg length)
            'c_adj': float, (leg 2 outer leg length)
            'd_adj': float  (leg 2 inner leg length) }) : length of triangle edges
        dimensions (dict{
            angle: float,
            height: float,
            thickness: float}): dimensions

    Returns:
        bpy.types.Object: object
    """
    triangles_1 = dimensions['triangles_1']
    triangles_2 = dimensions['triangles_2']
    angle = dimensions['angle']
    height = dimensions['height'] + 0.01
    thickness = dimensions['thickness']
    thickness_diff = dimensions['thickness_diff']

    turtle = bpy.context.scene.cursor
    orig_rot = turtle.location.copy()

    bm, obj = create_turtle('cutter')
    bm.select_mode = {'VERT'}

    # move turtle to slot start loc
    pu(bm)
    dn(bm, 0.01)
    rt(angle)
    fd(bm, triangles_1['a_adj'])
    lt(90)
    fd(bm, thickness_diff)
    lt(90)
    fd(bm, triangles_1['b_adj'])
    turtle.rotation_euler = orig_rot
    turtle_start_loc = turtle.location.copy()
    pd(bm)

    # draw leg_1
    add_vert(bm)
    rt(angle)
    fd(bm, triangles_2['a_adj'])
    lt(90)
    fd(bm, thickness)
    lt(90)
    fd(bm, triangles_2['b_adj'])

    bmesh.ops.contextual_create(
        bm,
        geom=bm.verts,
        mat_nr=0,
        use_smooth=False
    )
    bm_deselect_all(bm)
    home(obj)
    turtle.location = turtle_start_loc

    # draw leg 2
    add_vert(bm)
    fd(bm, triangles_2['c_adj'])
    rt(90)
    fd(bm, thickness)
    rt(90)
    fd(bm, triangles_2['d_adj'])
    bm.verts.ensure_lookup_table()
    verts = [v for v in bm.verts if v.index >= 3]

    bmesh.ops.contextual_create(
        bm,
        geom=verts,
        mat_nr=0,
        use_smooth=False
    )

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)

    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_corner_3D(triangles, dimensions):
    """Draw a corner (L) shape.

    Args:
        triangles (dict {
            'a_adj': float, (leg 1 outer leg length)
            'b_adj': float, (leg 1 inner leg length)
            'c_adj': float, (leg 2 outer leg length)
            'd_adj': float  (leg 2 inner leg length) }) : length of triangle edges
        dimensions (dict{
            angle: float,
            height: float,
            thickness: float}): dimensions

    Returns:
        bpy.types.Object: object
    """
    #  leg 2
    #    _
    #   | |
    #   | |
    #   | |_ _ _
    #   |_ _ _ _| leg 1

    angle = dimensions['angle']
    height = dimensions['height']
    thickness = dimensions['thickness']

    turtle = bpy.context.scene.cursor
    orig_rot = turtle.location.copy()

    bm, obj = create_turtle('L_2D')
    bm.select_mode = {'VERT'}

    # draw leg_1
    add_vert(bm)
    rt(angle)
    fd(bm, triangles['a_adj'])
    lt(90)
    fd(bm, thickness)
    lt(90)
    fd(bm, triangles['b_adj'])

    bmesh.ops.contextual_create(
        bm,
        geom=bm.verts,
        mat_nr=0,
        use_smooth=False
    )
    bm_deselect_all(bm)
    home(obj)
    turtle.rotation_euler = orig_rot

    # draw leg 2
    add_vert(bm)
    fd(bm, triangles['c_adj'])
    rt(90)
    fd(bm, thickness)
    rt(90)
    fd(bm, triangles['d_adj'])
    bm.verts.ensure_lookup_table()
    verts = [v for v in bm.verts if v.index >= 3]

    bmesh.ops.contextual_create(
        bm,
        geom=verts,
        mat_nr=0,
        use_smooth=False
    )

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)

    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_curved_cuboid(name, radius, segments, deg, height, width):
    """Draws a curved cuboid centered on the turtle

    Args:
        name (string): name
        radius (float): radius of inner edge
        segments (int): number of segments
        deg (float): degrees of arc to cover
        height (float): height
        width (float): width (distance from inner to outer edge)

    Returns:
        bpy.types.Object: Object
    """
    bm, obj = create_turtle(name)
    bm.select_mode = {'VERT'}
    arc(bm, radius, deg, segments)
    bm_deselect_all(bm)
    arc(bm, radius + width, deg, segments)
    bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, height, False)
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_rectangular_floor_core(dims, subdivs, margin=0.001):
    """Draws a rectangular floor core and assigns Verts to appropriate groups

    Args:
        dims (tuple[3]): Dimensions
        subdivs (tuple[3]): How many times to subdivide each face
        margin (float, optional): Margin to leave around textured areas
        to correct for displacement distortion.
        Defaults to 0.001.

    Returns:
        bpy.types.Object: Floor Core
    """
    vert_groups = ['Left', 'Right', 'Front', 'Back', 'Top', 'Bottom']
    bm, obj = create_turtle('Rectangular Floor', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # Start drawing core
    pd(bm)
    add_vert(bm)
    bm.select_mode = {'VERT'}

    # Draw front bottom edges
    ri(bm, margin)

    subdiv_x_dist = (dims[0] - (margin * 2)) / subdivs[0]

    i = 0
    while i < subdivs[0]:
        ri(bm, subdiv_x_dist)
        i += 1

    ri(bm, margin)

    # Select edge and extrude to create bottom
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    fd(bm, margin)

    subdiv_y_dist = (dims[1] - (margin * 2)) / subdivs[1]

    i = 0
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist)
        i += 1

    fd(bm, margin)

    # select bottom and extrude up
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, margin, False)

    subdiv_z_dist = (dims[2] - (margin * 2)) / subdivs[2]

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    up(bm, margin)

    # home turtle
    pu(bm)

    home(obj)

    # select left
    left_verts = select_verts_in_bounds(
        lbound=(0, 0, 0),
        ubound=(0, dims[1], dims[2]),
        buffer=margin / 2,
        bm=bm)

    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')

    # select Right
    right_verts = select_verts_in_bounds(
        lbound=(dims[1], 0, 0),
        ubound=(dims[1], dims[1], dims[2]),
        buffer=margin / 2,
        bm=bm)

    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')

    # Select Front
    front_verts = select_verts_in_bounds(
        lbound=(0, 0, 0),
        ubound=(dims[0], 0, dims[2]),
        buffer=margin / 2,
        bm=bm
    )

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')

    # Select back
    back_verts = select_verts_in_bounds(
        lbound=(0, dims[1], 0),
        ubound=(dims[0], dims[1], dims[2]),
        buffer=margin / 2,
        bm=bm
    )

    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')

    # Select top
    top_verts = select_verts_in_bounds(
        lbound=(0 + margin, 0 + margin, dims[2]),
        ubound=(dims[0] - margin, dims[1] - margin, dims[2]),
        buffer=margin / 2,
        bm=bm
    )

    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')

    # Select bottom
    bottom_verts = select_verts_in_bounds(
        lbound=(0 + margin, 0 + margin, 0),
        ubound=(dims[0] - margin, dims[1] - margin, 0),
        buffer=margin / 2,
        bm=bm
    )

    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj
