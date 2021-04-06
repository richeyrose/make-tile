from math import tan, radians, sqrt, sin
import bmesh
from mathutils import geometry
from ..lib.bmturtle.commands import (
    create_turtle,
    finalise_turtle,
    add_vert,
    fd,
    bk,
    ri,
    up,
    pu,
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
    points_are_inside_bmesh)


def draw_butterfly_base(self, context, margin=0.001):
    """Draw a butterfly style roof base.

    Args:
        context (bpy.Context): context
        margin (float, optional): Texture margin. Defaults to 0.001.
    """
    #
    #   |\      /|
    #   |B\c   / |
    #  a|  \  /  |
    #   |C_A\/___|
    #   | b      |
    #   |________|

    turtle = context.scene.cursor
    tile = context.collection
    tile_props = tile.mt_tile_props
    roof_tile_props = tile.mt_roof_tile_props

    base_dims = [s for s in tile_props.base_size]

    # Roof generator breaks if base height is less than this.
    if base_dims[2] < 0.002:
        base_dims[2] = 0.002

    # correct for inset (difference between standard base width and wall width) to take into account
    # displacement materials
    if roof_tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    if roof_tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist

    # Calculate triangle
    C = 90
    A = roof_tile_props.roof_pitch
    B = 180 - C - A
    b = base_dims[0] / 2
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)

    # subdivisions
    subdivs = self.get_subdivs(tile_props.subdivision_density, base_dims)

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
    if roof_tile_props.inset_x_neg:
        ri(bm, roof_tile_props.inset_dist)
    if roof_tile_props.inset_y_pos:
        fd(bm, roof_tile_props.inset_dist)

    draw_origin = turtle.location.copy()

    pd(bm)
    add_vert(bm)

    # Draw front bottom edge of base
    i = 0
    while i < 2:
        ri(bm, base_dims[0] / 2)
        i += 1

    # Select edge and extrude up
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)

    subdiv_z_dist = (base_dims[2] - (margin)) / subdivs[2]

    up(bm, margin)

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    bm_deselect_all(bm)

    # draw right peak
    bm.select_mode = {'VERT'}
    pd(bm)
    add_vert(bm)
    ptu(90)
    fd(bm, a)
    right_peak_loc = turtle.location.copy()
    yri(B + 180)
    fd(bm, c)
    right_nadir_loc = turtle.location.copy()
    pu(bm)

    # select last three verts
    bm.verts.ensure_lookup_table()
    tri_verts = bm.verts[-3:]
    for v in tri_verts:
        v.select_set(True)

    # create triangle and grid fill
    bmesh.ops.contextual_create(bm, geom=tri_verts, mat_nr=0, use_smooth=False)
    bm_deselect_all(bm)

    # slice margin
    # draw left peak
    bm.select_mode = {'VERT'}
    turtle.location = draw_origin
    turtle.rotation_euler = (0, 0, 0)
    pd(bm)
    up(bm, base_dims[2])
    pd(bm)
    add_vert(bm)
    ptu(90)
    fd(bm, a)
    left_peak_loc = turtle.location.copy()
    ylf(B + 180)
    fd(bm, c)
    left_nadir_loc = turtle.location.copy()
    # select last three verts
    bm.verts.ensure_lookup_table()
    tri_verts = bm.verts[-3:]
    for v in tri_verts:
        v.select_set(True)

    # create triangle and grid fill
    bmesh.ops.contextual_create(bm, geom=tri_verts, mat_nr=0, use_smooth=False)

    # clean up and merge with base bit
    bm.select_mode = {'VERT'}
    bm_select_all(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bm_deselect_all(bm)
    home(obj)

    bm.select_mode = {'FACE'}
    bm_select_all(bm)

    # extrude along y
    fd(bm, margin, del_original=False)
    subdiv_y_dist = (base_dims[1] - (margin * 2)) / (subdivs[1] - 1)

    i = 1
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist, del_original=True)
        i += 1
    fd(bm, margin, del_original=True)

    bm_deselect_all(bm)
    home(obj)

    # slice mesh to create margins
    turtle.location = draw_origin

    # base left
    plane = (
        turtle.location[0] + margin,
        turtle.location[1],
        turtle.location[2])

    bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
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
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        dist=margin / 4,
        plane_co=plane,
        plane_no=(1, 0, 0))

    bm_deselect_all(bm)

    # select left hand verts
    left_verts = select_verts_in_bounds(
        lbound=(
            turtle.location),
        ubound=(
            turtle.location[0] + base_dims[0] / 2,
            turtle.location[1] + base_dims[1],
            left_peak_loc[2]),
        buffer=margin,
        bm=bm)

    # calculate tri for left margin slice
    v1 = left_peak_loc
    v2 = left_nadir_loc
    v3 = (
        left_nadir_loc[0],
        left_nadir_loc[1] + base_dims[1],
        left_nadir_loc[2])

    # normal
    norm = geometry.normal((v1, v2, v3))

    # point on plane
    plane = (
        turtle.location[0] + base_dims[0] / 2 - margin,
        turtle.location[1],
        turtle.location[2] + base_dims[2])

    # ensure faces and edges are selected
    bm.select_mode = {'FACE'}
    bm.select_flush(True)
    left_edges = [e for e in bm.edges if e.select]
    left_faces = [f for f in bm.faces if f.select]

    # slice left roof margin
    bmesh.ops.bisect_plane(
        bm,
        geom=left_verts[:] + left_edges[:] + left_faces[:],
        dist=margin / 4,
        plane_co=plane,
        plane_no=norm)

    bm_deselect_all(bm)

    # select right hand verts
    bm.select_mode = {'VERT'}
    right_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0] + base_dims[0] / 2,
            turtle.location[1],
            turtle.location[2]),
        ubound=(
            turtle.location[0] + base_dims[0],
            turtle.location[1] + base_dims[1],
            right_peak_loc[2]),
        buffer=margin,
        bm=bm)

    # calculate tri for right margin slice
    v1 = right_peak_loc
    v2 = right_nadir_loc
    v3 = (
        right_nadir_loc[0],
        right_nadir_loc[1] + base_dims[1],
        right_nadir_loc[2])

    # normal
    norm = geometry.normal((v1, v2, v3))

    # point on plane
    plane = (
        turtle.location[0] + base_dims[0] / 2 + margin,
        turtle.location[1],
        turtle.location[2] + base_dims[2])

    # ensure faces and edges are selected
    bm.select_mode = {'FACE'}
    bm.select_flush(True)

    right_edges = [e for e in bm.edges if e.select]
    right_faces = [f for f in bm.faces if f.select]

    # slice left roof margin
    bmesh.ops.bisect_plane(
        bm,
        geom=right_verts[:] + right_edges[:] + right_faces[:],
        dist=margin / 4,
        plane_co=plane,
        plane_no=norm)

    bm_deselect_all(bm)

    # subdivide vertically
    norm = (1, 0, 0)

    subdiv_x_dist = (base_dims[0] - (margin * 2)) / subdivs[0]

    turtle.location = draw_origin
    pu(bm)
    ri(bm, margin)
    i = 0
    while i < subdivs[0]:
        ri(bm, subdiv_x_dist)
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            dist=margin / 4,
            plane_co=turtle.location,
            plane_no=norm)
        i += 1
    home(obj)

    # subdivide horizontally
    norm = (0, 0, 1)
    roof_height = left_peak_loc[2] - left_nadir_loc[2]
    subdiv_roof_dist = roof_height / (subdivs[0] / 2)
    up(bm, base_dims[2])
    i = 1
    while i < subdivs[0] / 2:
        up(bm, subdiv_roof_dist)
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            dist=margin,
            plane_co=turtle.location,
            plane_no=norm)
        i += 1
    home(obj)

    # create a temporary mesh for roof top selection
    #
    # _____C__b__A
    # \    |    /
    #  \  a|   /c
    #   \  |  /
    #    \ | /
    #     \|/
    #      B
    roof_a = a + margin * 2
    roof_c = (roof_a/sin(radians(A)) * sin(radians(C)))
    roof_b = (roof_c/sin(radians(C)) * sin(radians(B)))

    roof_bm = bmesh.new()
    roof_bm.select_mode = {'VERT'}

    turtle.location = draw_origin
    ri(roof_bm, base_dims[0] / 2)
    up(roof_bm, base_dims[2] - margin / 2)
    bk(roof_bm, 0.01)
    pd(roof_bm)
    add_vert(roof_bm)
    ptu(90)
    yri(B)
    fd(roof_bm, roof_c)
    ylf(180-A)
    fd(roof_bm, roof_b * 2)
    bm_select_all(roof_bm)
    bmesh.ops.contextual_create(
        roof_bm,
        geom=roof_bm.verts,
        mat_nr=0,
        use_smooth=False)
    turtle.rotation_euler = (0, 0, 0)
    roof_bm.select_mode = {'FACE'}
    bm_select_all(roof_bm)
    fd(roof_bm, base_dims[1] + 0.02, False)
    bmesh.ops.recalc_face_normals(roof_bm, faces=roof_bm.faces)

    # select all points in roof mesh that are inside gable mesh
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(
        bm_coords,
        roof_bm)
    for vert, select in zip(bm.verts, to_select):
        vert.select = select
    top_verts = [v for v in bm.verts if v.select]

    assign_verts_to_group(top_verts, obj, deform_groups, "Top")
    roof_bm.free()

    turtle.location = draw_origin
    turtle.rotation_euler = (0, 0, 0)

    # bottom verts
    bm_deselect_all(bm)
    bottom_verts = [v for v in bm.verts if v.co[2] == turtle.location[2]]
    assign_verts_to_group(bottom_verts, obj, deform_groups, "Bottom")
    bm_deselect_all(bm)

    # left verts
    left_verts = select_verts_in_bounds(
        lbound=(turtle.location),
        ubound=(
            turtle.location[0],
            turtle.location[1] + base_dims[1],
            turtle.location[2] + left_peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    left_verts = [v for v in bm.verts if v in left_verts and
                  v not in top_verts and
                  v not in bottom_verts]
    assign_verts_to_group(left_verts, obj, deform_groups, "Base Left")
    bm_deselect_all(bm)

    # right verts
    right_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0] + base_dims[0],
            turtle.location[1],
            turtle.location[2]),
        ubound=(
            turtle.location[0] + base_dims[0],
            turtle.location[1] + base_dims[1],
            turtle.location[2] + right_peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    right_verts = [v for v in bm.verts if v in right_verts and
                   v not in top_verts and
                   v not in bottom_verts]
    assign_verts_to_group(right_verts, obj, deform_groups, "Base Right")
    bm_deselect_all(bm)

    # select front verts
    front_verts = select_verts_in_bounds(
        lbound=(
            turtle.location),
        ubound=(
            turtle.location[0] + base_dims[0],
            turtle.location[1],
            left_peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    front_verts = [v for v in bm.verts if v in front_verts and
                   v not in top_verts and
                   v not in bottom_verts and
                   v not in left_verts and
                   v not in right_verts]
    assign_verts_to_group(front_verts, obj, deform_groups, "Gable Front")
    bm_deselect_all(bm)

    # select back verts
    back_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0],
            turtle.location[1] + base_dims[1],
            turtle.location[2]),
        ubound=(
            turtle.location[0] + base_dims[0],
            turtle.location[1] + base_dims[1],
            left_peak_loc[2]),
        buffer=margin / 2,
        bm=bm)
    back_verts = [v for v in bm.verts if v in back_verts and
                  v not in top_verts and
                  v not in bottom_verts and
                  v not in left_verts and
                  v not in right_verts]
    assign_verts_to_group(back_verts, obj, deform_groups, "Gable Back")
    bm_deselect_all(bm)

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)
    return obj


def draw_butterfly_roof_top(self, context, margin=0.001):
    """Draw a butterfly type roof top.

    Args:
        context (bpy.context): context
        margin (float, optional): Margin around textured area. Defaults to 0.001.
    """
    # Base tri
    #         C__b__A
    #   |\    |    /|
    #   | \  a|   /c|
    #   |  \  |  /  |
    #   |   \ | /   |
    #   |____\|/____|
    #   |     B     |
    #   |___________|

    turtle = context.scene.cursor
    tile = context.collection
    tile_props = tile.mt_tile_props
    roof_tile_props = tile.mt_roof_tile_props

    base_dims = [s for s in tile_props.base_size]

    # correct for inset (difference between standard base width and wall width) to take into account
    # displacement materials
    if roof_tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    if roof_tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist

    # Calculate triangle
    C = 90
    A = roof_tile_props.roof_pitch
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

    # Side eaves
    #
    #
    #          B
    #         /|
    #        / |
    #     c /  | a
    #      /   |
    #     /____|
    #    A  b = side_eaves
    #   /|
    #  / |

    b = roof_tile_props.side_eaves
    a = (b/sin(radians(B)) * sin(radians(A)))
    c = (b/sin(radians(B)) * sin(radians(C)))
    eaves_tri = {
        'a': a,
        'b': b,
        'c': c}

    # roof_bottom
    #        C ___b___ A
    #         |      /
    #         |     /
    #   |\    |    /|
    #   | \  a|   /c|
    #   |  \  |  /  |
    #   |   \ | /   |
    #   |____\|/____|
    #   |     B     |
    #   |___________|

    c = eaves_tri['c'] + base_tri['c']
    a = (c/sin(radians(C)) * sin(radians(A)))
    b = (c/sin(radians(C)) * sin(radians(B)))
    roof_bottom = {
        'a': a,
        'b': b,
        'c': c}

    # roof thickness (we want to move up by c)
    C = 90
    B = 90 - B
    A = 180 - C - B
    b = roof_tile_props.roof_thickness
    a = tan(radians(A)) * b
    c = sqrt(a**2 + b**2)
    peak_tri = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    # subdivisions
    density = tile_props.subdivision_density
    subdivs = self.get_subdivs(density, base_dims)

    for index, value in enumerate(subdivs):
        if value == 0:
            subdivs[index] = 1

    subdiv_x_dist = (roof_bottom['c'] - margin) / subdivs[0]
    subdiv_y_dist = (
        base_dims[1] - (margin * 2) + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos) / subdivs[1]

    vert_groups = ['Left', 'Right']
    bm, obj = create_turtle('Roof Top', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # start
    # check to see if we're correcting for wall thickness
    if roof_tile_props.inset_y_pos:
        fd(bm, roof_tile_props.inset_dist)

    # draw gable end edges
    bk(bm, roof_tile_props.end_eaves_neg)
    up(bm, base_dims[2])
    ri(bm, base_dims[0] / 2 + roof_tile_props.inset_dist)

    draw_origin = turtle.location.copy()
    pd(bm)

    add_vert(bm)
    ptu(90)
    yri(base_tri['B'])
    i = 0
    while i < subdivs[0]:
        fd(bm, subdiv_x_dist)
        i += 1
    right_peak_loc = turtle.location.copy()
    right_peak_loc[1] = right_peak_loc[1] + margin
    right_peak_loc[2] = right_peak_loc[2] + peak_tri['c']
    fd(bm, margin)
    turtle.location = draw_origin
    turtle.rotation_euler = (0, 0, 0)
    bm_deselect_all(bm)
    bm.verts.ensure_lookup_table()
    bm.verts[0].select = True
    ptu(90)
    ylf(base_tri['B'])
    i = 0
    while i < subdivs[0]:
        fd(bm, subdiv_x_dist)
        i += 1
    left_peak_loc = turtle.location.copy()
    left_peak_loc[1] = left_peak_loc[1] + margin
    left_peak_loc[2] = left_peak_loc[2] + peak_tri['c']
    fd(bm, margin)
    turtle.rotation_euler = (0, 0, 0)
    bm.select_mode = {'EDGE'}
    bm_select_all(bm)
    up(bm, peak_tri['c'])
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    fd(bm, margin, False)
    i = 0
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist)
        i += 1
    fd(bm, margin)
    bm_deselect_all(bm)
    home(obj)

    # create temporary bmesh to create verts groups
    left_bm = bmesh.new()
    left_bm.select_mode = {'VERT'}
    select_origin = (
        draw_origin[0] + margin / 4,
        draw_origin[1] + margin / 4,
        draw_origin[2] + peak_tri['c'] - margin / 2)
    turtle.location = select_origin
    pd(left_bm)
    add_vert(left_bm)
    ptu(90)
    ylf(base_tri['B'])
    fd(left_bm, roof_bottom['c'])
    left_bm.select_mode = {'EDGE'}
    bm_select_all(left_bm)
    turtle.rotation_euler = (0, 0, 0)
    up(left_bm, 0.1)
    left_bm.select_mode = {'FACE'}
    bm_select_all(left_bm)
    fd(left_bm, (base_dims[1] - (margin) + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos), False)
    bmesh.ops.recalc_face_normals(left_bm, faces=left_bm.faces)

    # select all points inside left_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, left_bm)
    # filter
    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] <= select_origin[0] + margin and \
                vert.co[2] >= select_origin[2] - margin:
            vert.select = select

    left_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')

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

    bm_deselect_all(bm)
    # filter
    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] >= select_origin[0] - margin and \
                vert.co[2] >= select_origin[2] - margin:
            vert.select = select

    right_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(right_verts, obj, deform_groups, "Right")
    bm_deselect_all(bm)

    # finalise turtle and release bmesh
    left_bm.free()
    finalise_turtle(bm, obj)
    return obj
