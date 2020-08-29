import bmesh
from .commands import (
    create_turtle,
    finalise_turtle,
    add_vert,
    fd,
    ri,
    up,
    pu,
    pd,
    home,
    arc)
from .helpers import (
    bm_select_all,
    bm_deselect_all,
    assign_verts_to_group,
    select_verts_in_bounds)


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
    pd()
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
    buffer = 0.001

    left_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')

    # select right side and assign to vert group
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = 0.001

    right_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')

    # select front side and assign to vert group
    lbound = (margin, 0, margin)
    ubound = (dims[0] - margin, 0, dims[2] - margin)
    buffer = 0.0001

    front_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')

    # select back side and assign to vert group
    lbound = (margin, dims[1], margin)
    ubound = (dims[0] - margin, dims[1], dims[2] - margin)
    buffer = 0.0001

    back_verts = select_verts_in_bounds(lbound, ubound, buffer, bm)
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def draw_curved_cuboid(name, radius, segments, degrees, height, width):
    """Draws a curved cuboid centered on the turtle

    Args:
        name (string): name
        radius (float): radius of inner edge
        segments (int): number of segments
        degrees (float): degrees of arc to cover
        height (float): height
        width (float): width (distance from inner to outer edge)

    Returns:
        bpy.types.Object: Object
    """
    bm, obj = create_turtle(name)
    bm.select_mode = {'VERT'}
    arc(bm, radius, degrees, segments)
    bm_deselect_all(bm)
    arc(bm, radius + width, degrees, segments)
    bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd()
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
    pd()
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
