from math import cos, acos, sqrt, degrees, radians
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
    dijkstra)


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
    support_w = 0.12  # width of corner supports
    support_h = 0.056

    b = dimensions['b']
    c = dimensions['c']
    A = dimensions['A']

    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    turtle = bpy.context.scene.cursor
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

    # assign top and bottom verts to vertex groups
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')

    # home turtle
    pu(bm)

    home(obj)

    # select left side and assign to vert group
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')

    # select right side and assign to vert group
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')

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


def draw_corner_floor_core(
        triangles,
        angle,
        thickness,
        height,
        native_subdivisions,
        margin=0.001):
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

    add_vert(bm)
    # draw leg 1
    # outer edge
    rt(angle)
    subdiv_dist = (triangles['a_adj'] - margin) / native_subdivisions[0]

    i = 0
    while i < native_subdivisions[0]:
        fd(bm, subdiv_dist)
        i += 1
    fd(bm, margin)
    leg_1_outer_vert_locs = [v.co for v in verts]

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
    subdiv_dist = (triangles['b_adj'] - margin) / native_subdivisions[0]
    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    fd(bm, margin)
    i = 0
    while i < native_subdivisions[0]:
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
    subdiv_dist = (triangles['c_adj'] - margin) / native_subdivisions[1]

    # outer
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_2_outer_vert_locs.append(verts[-1].co.copy())
    start_index = verts[-1].index

    i = 0
    while i < native_subdivisions[1]:
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
    subdiv_dist = (triangles['d_adj'] - margin) / native_subdivisions[1]
    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    fd(bm, margin)
    i = 0
    while i < native_subdivisions[1]:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_2_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)
    ret = bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bmesh.ops.subdivide_edges(bm, edges=ret['edges'], smooth=1, smooth_falloff='LINEAR', cuts=native_subdivisions[2])

    bmesh.ops.inset_region(bm, faces=bm.faces, use_even_offset=True, thickness=margin, use_boundary=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    # Z
    subdiv_dist = (height - (margin * 2)) / native_subdivisions[3]
    bm_select_all(bm)
    bm.select_mode={'FACE'}

    up(bm, margin, False)

    i = 0
    while i < native_subdivisions[3]:
        up(bm, subdiv_dist)
        i += 1
    up(bm, margin)

    # assign vertex groups
    # sides
    sides = {
        'Leg 1 Inner': leg_1_inner_vert_locs,
        'Leg 2 Inner': leg_2_inner_vert_locs,
        'Leg 1 Outer': leg_1_outer_vert_locs,
        'Leg 2 Outer': leg_2_outer_vert_locs}

    for key, value in sides.items():
        vert_group = []
        for loc in value:
            verts = select_verts_in_bounds(
                lbound=loc,
                ubound=(loc[0], loc[1], loc[2] + height),
                buffer=margin / 2,
                bm=bm)
            vert_group.extend(verts)
        assign_verts_to_group(vert_group, obj, deform_groups, key)

    # ends
    ends = {
        'Leg 1 End': leg_1_end_vert_locs,
        'Leg 2 End': leg_2_end_vert_locs}

    bm_deselect_all(bm)
    subdiv_dist = height / native_subdivisions[3]
    v1 = select_verts_in_bounds(leg_1_end_vert_locs[0], leg_1_end_vert_locs[0], margin, bm)
    v2 = select_verts_in_bounds(leg_1_end_vert_locs[1], leg_1_end_vert_locs[1], margin, bm)

    nodes = dijkstra(bm, v1[0], v2[0])
    node = nodes[v2[0]]

    for e in node.shortest_path:
        e.select_set(True)
    bm.select_flush(True)
    '''
    leg_1_outer_verts = []
    for loc in leg_1_outer_vert_locs:
        verts = select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm)
        leg_1_outer_verts.extend(verts)
    assign_verts_to_group(leg_1_outer_verts, obj, deform_groups, 'Leg 1 Outer')

    leg_2_outer_verts = []
    for loc in leg_2_outer_vert_locs:
        verts = select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm)
        leg_2_outer_verts.extend(verts)
    assign_verts_to_group(leg_2_outer_verts, obj, deform_groups, 'Leg 2 Outer')

    leg_1_inner_verts = []
    for loc in leg_1_inner_vert_locs:
        verts = select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm)
        leg_1_inner_verts.extend(verts)
    assign_verts_to_group(leg_1_inner_verts, obj, deform_groups, 'Leg 1 Inner')
    '''
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_corner_3D(triangles, dimensions):
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
    orig_loc = turtle.location.copy()
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


def draw_corner_2D(triangles, dimensions, thickness, return_locs=False):
    pass



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
