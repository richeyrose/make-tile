from math import radians, tan, sqrt
from mathutils import geometry
import bmesh
import bpy
from ..lib.bmturtle.commands import (
    create_turtle,
    finalise_turtle,
    add_vert,
    fd,
    bk,
    lf,
    ri,
    up,
    dn,
    pd,
    ptu,
    ylf,
    yri,
    home)

from ..lib.bmturtle.helpers import (
    bm_select_all,
    bm_deselect_all,
    assign_verts_to_group,
    select_verts_in_bounds,
    select_edges_in_bounds,
    points_are_inside_bmesh)

from .create_tile import get_subdivs

# from line_profiler import LineProfiler
# from os.path import splitext
# profile = LineProfiler()


# @profile
def draw_apex_base(self, tile_props, margin=0.001):
    """Draw an apex style roof base."""
    #      B
    #     /|\
    #    / | \c
    #   / a|  \
    #  /___|___\A
    #  |   C b |
    #  |_______|
    #     base
    turtle = bpy.context.scene.cursor
    # roof_tile_props = tile.mt_roof_tile_props

    base_dims = [s for s in tile_props.base_size]

    # Roof generator breaks if base height is less than this.
    if base_dims[2] < 0.002:
        base_dims[2] = 0.002

    # correct for inset (difference between standard base width and wall width) to take into account
    # displacement materials
    if tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] - tile_props.inset_dist
    if tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] - tile_props.inset_dist
    if tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] - tile_props.inset_dist
    if tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] - tile_props.inset_dist

    # Calculate triangle
    C = 90
    A = tile_props.roof_pitch
    B = 180 - C - A
    b = base_dims[0] / 2
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)

    # subdivisions
    subdivs = get_subdivs(tile_props.subdivision_density, base_dims)

    for index, value in enumerate(subdivs):
        if value == 0:
            subdivs[index] = 1

    # Create bmesh and object
    vert_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back', 'Bottom', 'Top']
    bm, obj = create_turtle('Base', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # start drawing
    # check to see if we're correcting for wall thickness
    if tile_props.inset_x_neg:
        ri(bm, tile_props.inset_dist)
    if tile_props.inset_y_pos:
        fd(bm, tile_props.inset_dist)

    draw_origin = turtle.location.copy()

    pd(bm)
    add_vert(bm)

    # Draw front bottom edge of base
    i = 0
    while i < subdivs[0]:
        ri(bm, base_dims[0] / subdivs[0])
        i += 1

    # Select edge and extrude up
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)

    subdiv_z_dist = (base_dims[2] - margin) / subdivs[2]
    up(bm, margin)

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    bm_deselect_all(bm)

    # draw peak
    bm.select_mode = {'VERT'}
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    ptu(90)
    ylf(90 - A)
    fd(bm, c)
    peak_loc = turtle.location.copy()
    yri(B * 2 + 180)
    fd(bm, c)

    # select last three verts
    bm.verts.ensure_lookup_table()
    tri_verts = bm.verts[-3:]
    for v in tri_verts:
        v.select_set(True)

    # create triangle and grid fill
    bmesh.ops.contextual_create(bm, geom=tri_verts, mat_nr=0, use_smooth=False)
    bm.select_mode = {'EDGE'}
    tri_edges = [e for e in bm.edges if e.select]
    bmesh.ops.subdivide_edges(bm, edges=tri_edges, cuts=subdivs[0] - 1, use_grid_fill=True)

    # clean up and merge with base bit
    bm.select_mode = {'VERT'}
    bm_select_all(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm_deselect_all(bm)
    home(obj)

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    bm.select_flush(True)
    # extrude along y
    fd(bm, margin, del_original=False)
    fd(bm, base_dims[1] - (margin * 2), del_original=True)
    fd(bm, margin, del_original=True)
    bm_deselect_all(bm)

    # select edges to split
    bm.select_mode = {'EDGE'}
    exclude_1 = select_edges_in_bounds(
        lbound=draw_origin,
        ubound=(
            draw_origin[0] + base_dims[0],
            draw_origin[1] + margin,
            peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    exclude_2 = select_edges_in_bounds(
        lbound=(
            draw_origin[0],
            draw_origin[1] + base_dims[1] - margin,
            draw_origin[2]),
        ubound=(
            draw_origin[0] + base_dims[0],
            draw_origin[1] + base_dims[1],
            peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    bm_deselect_all(bm)
    edges_to_split = select_edges_in_bounds(
        lbound=(
            draw_origin[0],
            draw_origin[1] + margin,
            draw_origin[2]),
        ubound=(
            draw_origin[0] + base_dims[0],
            draw_origin[1] + base_dims[1] - margin,
            peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    edges = [e for e in edges_to_split if e.select and e not in exclude_1 and e not in exclude_2]
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=subdivs[1] - 1, use_grid_fill=True)
    bm_deselect_all(bm)
    bm.select_mode = {'VERT'}
    home(obj)

    # slice mesh to create margins
    turtle.location = draw_origin
    geo = bm.verts[:] + bm.edges[:] + bm.faces[:]

    # base left
    plane = (
        turtle.location[0] + margin,
        turtle.location[1],
        turtle.location[2])

    bmesh.ops.bisect_plane(
        bm,
        geom=geo,
        dist=margin / 4,
        plane_co=plane,
        plane_no=(1, 0, 0))

    # base right
    plane = (
        turtle.location[0] + base_dims[0] - margin,
        turtle.location[1],
        turtle.location[2])

    bmesh.ops.bisect_plane(
        bm,
        geom=geo,
        dist=margin / 4,
        plane_co=plane,
        plane_no=(1, 0, 0))

    # roof left
    v1 = (
        turtle.location[0],
        turtle.location[1],
        turtle.location[2] + base_dims[2])
    v2 = (
        turtle.location[0] + (base_dims[0] / 2),
        turtle.location[1],
        turtle.location[2] + base_dims[2] + a)
    v3 = (
        turtle.location[0] + (base_dims[0] / 2),
        turtle.location[1] + base_dims[1],
        turtle.location[2] + base_dims[2] + a)

    norm = geometry.normal((v1, v2, v3))

    plane = (
        turtle.location[0] + margin,
        turtle.location[1],
        turtle.location[2] + base_dims[2])

    geo = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(
        bm,
        geom=geo,
        dist=margin / 4,
        plane_co=plane,
        plane_no=norm)

    # roof right
    v1 = (
        turtle.location[0] + base_dims[0],
        turtle.location[1],
        turtle.location[2] + base_dims[2])
    v2 = (
        turtle.location[0] + (base_dims[0] / 2),
        turtle.location[1],
        turtle.location[2] + base_dims[2] + a)
    v3 = (
        turtle.location[0] + (base_dims[0] / 2),
        turtle.location[1] + base_dims[1],
        turtle.location[2] + base_dims[2] + a)

    norm = geometry.normal((v1, v2, v3))

    plane = (
        turtle.location[0] + base_dims[0] - margin,
        turtle.location[1],
        turtle.location[2] + base_dims[2])

    geo = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(
        bm,
        geom=geo,
        dist=margin / 4,
        plane_co=plane,
        plane_no=norm)

    # create a temporary bmesh for gable ends to select verts inside and create vert groups
    gable_bm = bmesh.new()
    gable_base_dims = base_dims
    gable_base_dims[0] = base_dims[0] - margin
    gable_base_dims[2] = base_dims[2] - margin / 2
    gable_b = gable_base_dims[0] / 2
    gable_a = tan(radians(A)) * gable_b
    gable_c = sqrt(gable_a**2 + gable_b**2)

    gable_bm.select_mode = {'VERT'}
    bk(gable_bm, margin)
    ri(gable_bm, margin / 2)
    up(gable_bm, margin / 2)

    pd(gable_bm)
    add_vert(gable_bm)
    ri(gable_bm, gable_base_dims[0])
    up(gable_bm, gable_base_dims[2])

    ptu(90)
    ylf(90 - A)
    fd(gable_bm, gable_c)
    yri(B * 2 + 180)
    fd(gable_bm, gable_c)

    turtle.rotation_euler = (0, 0, 0)
    bm_select_all(gable_bm)
    bmesh.ops.contextual_create(gable_bm, geom=gable_bm.verts, mat_nr=0, use_smooth=False)

    gable_bm.select_mode = {'FACE'}
    bm_select_all(gable_bm)
    fd(gable_bm, margin * 2, False)
    bmesh.ops.recalc_face_normals(gable_bm, faces=gable_bm.faces)

    # select all points in roof mesh that are inside gable mesh
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, gable_bm)

    # points_are_inside isn't perfect on low poly meshes so filter out false positives here
    for vert, select in zip(bm.verts, to_select):
        if vert.co[1] < draw_origin[1] + margin / 2:
            vert.select = select
    front_verts = [v for v in bm.verts if v.select]
    bm_deselect_all(bm)

    # Gable Back
    # move gable mesh to other end
    for v in gable_bm.verts:
        v.co[1] = v.co[1] + base_dims[1]

    to_select = points_are_inside_bmesh(bm_coords, gable_bm)
    for vert, select in zip(bm.verts, to_select):
        if vert.co[1] > base_dims[1] - margin / 2:
            vert.select = select

    back_verts = [v for v in bm.verts if v.select]

    # Free gable bmesh as we don't need it any more
    gable_bm.free()

    bm_deselect_all(bm)
    turtle.location = draw_origin

    # Base Left
    left_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0] - margin,
            turtle.location[1],
            turtle.location[2] + margin),
        ubound=(
            turtle.location[0],
            turtle.location[1] + base_dims[1],
            turtle.location[2] + base_dims[2] - margin / 2),
        buffer=margin / 2,
        bm=bm)

    assign_verts_to_group(left_verts, obj, deform_groups, "Base Left")
    bm_deselect_all(bm)

    # Base Right
    right_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0] + base_dims[0] + margin / 2,
            turtle.location[1],
            turtle.location[2] + margin),
        ubound=(
            turtle.location[0] + base_dims[0] + margin,
            turtle.location[1] + base_dims[1],
            turtle.location[2] + base_dims[2] - margin / 2),
        buffer=margin / 3,
        bm=bm)

    assign_verts_to_group(right_verts, obj, deform_groups, "Base Right")
    bm_deselect_all(bm)

    # Base bottom
    bottom_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0],
            turtle.location[1],
            turtle.location[2]),
        ubound=(
            turtle.location[0] + base_dims[0] + margin,
            turtle.location[1] + base_dims[1],
            turtle.location[2]),
        buffer=margin / 3,
        bm=bm)
    assign_verts_to_group(bottom_verts, obj, deform_groups, "Bottom")
    bm_deselect_all(bm)

    # EXPENSIVE!
    verts = bottom_verts + left_verts + right_verts + front_verts + back_verts
    top_verts = [v for v in bm.verts if v not in verts]
    assign_verts_to_group(top_verts, obj, deform_groups, "Top")

    # Additional filter for gables
    verts = left_verts + right_verts + bottom_verts
    front_verts = [v for v in bm.verts if v in front_verts and v not in verts]
    assign_verts_to_group(front_verts, obj, deform_groups, "Gable Front")
    back_verts = [v for v in bm.verts if v in back_verts and v not in verts]
    assign_verts_to_group(back_verts, obj, deform_groups, "Gable Back")

    turtle.location = (0, 0, 0)
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)
    # profile.dump_stats(splitext(__file__)[0] + '.prof')
    return obj


# @profile
def draw_apex_roof_top(self, tile_props, margin=0.001):
    """Draw an apex type roof top.

    Args:
        context (bpy.context): context
        margin (float, optional): Margin around textured area. Defaults to 0.001.
    """
    #      B
    #     /|\
    #    / | \c
    #   / a|  \
    #  /___|___\A
    #  |   C b |
    #  |_______|
    #     base

    turtle = bpy.context.scene.cursor
    # roof_tile_props = tile.mt_roof_tile_props

    base_dims = [s for s in tile_props.base_size]

    # correct for inset (difference between standard base width and wall width) to take into account
    # displacement materials
    if tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] - tile_props.inset_dist
    if tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] - tile_props.inset_dist
    if tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] - tile_props.inset_dist
    if tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] - tile_props.inset_dist

    # calculate triangle
    C = 90
    A = tile_props.roof_pitch
    B = 180 - C - A
    b = base_dims[0] / 2
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)

    base_tri = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    # side eaves distance is vertical distance down from C
    #       B
    #       |\
    #     a | \c
    #       |_ \
    #       |_|_\A
    #      C  b

    a = base_tri['a'] + tile_props.side_eaves
    C = 90
    A = tile_props.roof_pitch
    B = 180 - 90 - A
    b = a / tan(radians(A))
    c = sqrt(a**2 + b**2)

    inner_tri = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    # calculate size of peak triangle based on roof thickness
    #        B
    #       /|
    #    c / |
    #     /  |a
    #    /___|
    #   A  b  C
    C = 90
    B = tile_props.roof_pitch / 2
    A = 180 - 90 - B
    b = tile_props.roof_thickness
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)

    peak_tri = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    # calculate size of eave end triangle based on roof thickness
    C = 90
    A = tile_props.roof_pitch
    B = 180 - C - A
    a = tile_props.roof_thickness
    b = a / tan(radians(A))
    c = sqrt(a**2 + b**2)

    eave_end_tri = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    # calculate size of outer roof triangle
    #       B
    #       |\
    #     a | \c
    #       |_ \
    #       |_|_\A
    #      C  b

    C = 90
    A = tile_props.roof_pitch
    B = 180 - A - C
    b = inner_tri['b'] + eave_end_tri['c']
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)

    outer_tri = {
        'A': A,
        'B': B,
        'C': C,
        'a': a,
        'b': b,
        'c': c}

    # subdivisions
    density = tile_props.subdivision_density
    subdivs = get_subdivs(density, base_dims)

    vert_groups = ['Left', 'Right']
    bm, obj = create_turtle('Roof', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # start
    # check to see if we're correcting for wall thickness
    if tile_props.inset_x_neg:
        ri(bm, tile_props.inset_dist)
    if tile_props.inset_y_pos:
        fd(bm, tile_props.inset_dist)

    # draw gable end edges
    draw_origin = turtle.location.copy()

    bk(bm, tile_props.end_eaves_neg)
    ri(bm, base_dims[0] / 2)
    lf(bm, inner_tri['b'])
    up(bm, base_dims[2] - tile_props.side_eaves)

    draw_origin = turtle.location.copy()

    ptu(90)
    yri(90 - inner_tri['A'])
    pd(bm)

    # vert 0
    add_vert(bm)
    # vert 1
    fd(bm, inner_tri['c'])
    ylf(inner_tri['B'] * 2 - 180)
    # vert 2
    fd(bm, inner_tri['c'])
    turtle.rotation_euler = (0, 0, 0)
    # vert 3
    ri(bm, eave_end_tri['c'])
    bm.verts.ensure_lookup_table()
    vert_3_loc = bm.verts[-1].co.copy()
    ptu(90)
    ylf(90 - inner_tri['A'])
    # vert 4
    fd(bm, outer_tri['c'])
    bm.verts.ensure_lookup_table()
    apex_loc = bm.verts[-1].co.copy()

    yri(outer_tri['B'] * 2 + 180)
    # vert 5
    fd(bm, outer_tri['c'])
    bm.verts.ensure_lookup_table()
    vert_5_loc = bm.verts[-1].co.copy()
    turtle.location = (0, 0, 0)
    turtle.rotation_euler = (0, 0, 0)

    # create gable end left face
    bm.verts.ensure_lookup_table()
    verts = [v for v in bm.verts if v.index in [0, 1, 4, 5]]
    bmesh.ops.contextual_create(bm, geom=verts, mat_nr=0, use_smooth=False)

    # loopcut edges
    edges = [e for e in bm.edges if e.index in [0, 4]]
    bmesh.ops.subdivide_edges(
        bm,
        edges=edges,
        cuts=subdivs[0] - 1,
        smooth_falloff='INVERSE_SQUARE',
        use_grid_fill=True)

    # create gable end right face
    verts = [v for v in bm.verts if v.index in [1, 2, 3, 4]]
    bmesh.ops.contextual_create(bm, geom=verts, mat_nr=0, use_smooth=False)

    # loopcut edges
    edges = [e for e in bm.edges if e.index in [1, 3]]
    bmesh.ops.subdivide_edges(
        bm,
        edges=edges,
        cuts=subdivs[0] - 1,
        smooth_falloff='INVERSE_SQUARE',
        use_grid_fill=True)

    # margin cut for bottom of roof
    plane = (
        draw_origin[0],
        draw_origin[1],
        draw_origin[2] + margin)

    bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        dist=margin / 4,
        plane_co=plane,
        plane_no=(0, 0, 1))

    # extrude along y
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    fd(bm, margin, del_original=False)
    fd(bm, base_dims[1] - (margin * 2) + tile_props.end_eaves_neg + tile_props.end_eaves_pos)
    fd(bm, margin, del_original=True)
    bm_deselect_all(bm)

    bm.select_mode = {'EDGE'}
    exclude_1 = select_edges_in_bounds(
        lbound=vert_5_loc,
        ubound=(
            vert_3_loc[0],
            vert_5_loc[1] + margin,
            apex_loc[2]),
        buffer=margin / 2,
        bm=bm)
    exclude_2 = select_edges_in_bounds(
        lbound=(
            vert_5_loc[0],
            vert_5_loc[1] + base_dims[1] - margin + tile_props.end_eaves_neg + tile_props.end_eaves_pos,
            vert_5_loc[2]),
        ubound=(
            vert_3_loc[0],
            vert_5_loc[1] + base_dims[1] + tile_props.end_eaves_neg + tile_props.end_eaves_pos,
            apex_loc[2]),
        buffer=margin / 2,
        bm=bm)
    bm_deselect_all(bm)
    edges_to_split = select_edges_in_bounds(
        lbound=(
            vert_5_loc[0],
            vert_5_loc[1] + margin,
            vert_5_loc[2]),
        ubound=(
            vert_3_loc[0],
            vert_5_loc[1] + base_dims[1] + tile_props.end_eaves_neg + tile_props.end_eaves_pos,
            apex_loc[2]),
        buffer=margin / 2,
        bm=bm)

    edges = [e for e in edges_to_split if e.select and e not in exclude_1 and e not in exclude_2]
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=subdivs[1] - 1, use_grid_fill=True)
    bm_deselect_all(bm)
    bm.select_mode = {'VERT'}
    # create bmesh for selecting left roof
    left_bm = bmesh.new()
    turtle.location = draw_origin
    left_bm.select_mode = {'VERT'}
    lf(left_bm, eave_end_tri['c'])
    dn(left_bm, margin)
    bk(left_bm, margin)
    ptu(90)
    yri(90 - inner_tri['A'])
    pd(left_bm)
    add_vert(left_bm)
    fd(left_bm, outer_tri['c'] + margin * 4)
    ylf(90)
    left_bm.select_mode = {'EDGE'}
    bm_select_all(left_bm)
    fd(left_bm, margin * 4)
    left_bm.select_mode = {'FACE'}
    turtle.rotation_euler = (0, 0, 0)
    bm_select_all(left_bm)
    fd(left_bm, base_dims[1] + tile_props.end_eaves_neg + tile_props.end_eaves_pos + margin * 4, False)
    bmesh.ops.recalc_face_normals(left_bm, faces=left_bm.faces)

    # select all points inside left_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, left_bm)

    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] < apex_loc[0] + margin and \
            vert.co[2] > draw_origin[2] + margin / 4 and \
                vert.co[1] > draw_origin[1] + margin / 4 and \
                    vert.co[1] < draw_origin[1] + base_dims[1] + tile_props.end_eaves_neg + tile_props.end_eaves_pos - (margin / 4):
            vert.select = select

    left_verts = [v for v in bm.verts if v.select]

    assign_verts_to_group(left_verts, obj, deform_groups, "Left")
    bm_deselect_all(bm)

    # mirror selector mesh
    ret = bmesh.ops.mirror(
        left_bm,
        geom=left_bm.verts[:] + left_bm.edges[:] + left_bm.faces[:],
        merge_dist=0,
        axis='X')

    verts = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]

    for v in left_bm.verts:
        if v not in verts:
            left_bm.verts.remove(v)

    for v in left_bm.verts:
        v.co[0] = v.co[0] + tile_props.base_size[0]
    bmesh.ops.recalc_face_normals(left_bm, faces=left_bm.faces)

    # select all points inside right_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, left_bm)

    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] > apex_loc[0] - margin and \
            vert.co[2] > draw_origin[2] + margin / 4 and \
                vert.co[1] > draw_origin[1] + margin / 4 and \
                    vert.co[1] < draw_origin[1] + base_dims[1] + tile_props.end_eaves_neg + tile_props.end_eaves_pos - (margin / 4):
            vert.select = select

    right_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(right_verts, obj, deform_groups, "Right")
    bm_deselect_all(bm)

    # finalise turtle and release bmesh
    left_bm.free()

    finalise_turtle(bm, obj)
    # profile.dump_stats(splitext(__file__)[0] + '.prof')
    return obj
