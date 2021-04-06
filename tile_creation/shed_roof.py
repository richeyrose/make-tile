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
    pu,
    pd,
    ptu,
    ptd,
    ylf,
    yri,
    home,
    arc,
    rt,
    lt)

from ..lib.bmturtle.helpers import (
    bm_select_all,
    bm_deselect_all,
    assign_verts_to_group,
    select_verts_in_bounds,
    points_are_inside_bmesh)

from ..lib.bmturtle.scripts import draw_cuboid

def draw_shed_base(context, margin=0.001):
    """Draw a shed style roof base (Not sure why this style is called "shed" but hey ho)."""
    #  B
    #  |\
    # a| \c
    #  |__\A
    #  C b |
    #  |___|
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
    b = base_dims[0]
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
    if roof_tile_props.inset_x_neg:
        ri(bm, roof_tile_props.inset_dist)
    if roof_tile_props.inset_y_pos:
        fd(bm, roof_tile_props.inset_dist)

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

    subdiv_z_dist = (base_dims[2] - (margin * 2)) / subdivs[2]

    up(bm, margin)

    i = 0
    while i < subdivs[2]:
        up(bm, subdiv_z_dist)
        i += 1

    up(bm, margin)

    bm_deselect_all(bm)

    # draw peak
    bm.select_mode = {'VERT'}
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    ptu(90)
    ylf(90 - A)
    fd(bm, c)
    # save location of peak
    peak_loc = turtle.location.copy()
    yri(B + 180)
    fd(bm, a)

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

    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=margin / 4, plane_co=plane, plane_no=(1, 0, 0))

    # base right
    plane = (
        turtle.location[0] + base_dims[0] - margin,
        turtle.location[1],
        turtle.location[2])

    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=margin / 4, plane_co=plane, plane_no=(1, 0, 0))

    # roof right
    v1 = (
        turtle.location[0] + base_dims[0],
        turtle.location[1],
        turtle.location[2] + base_dims[2])
    v2 = (
        turtle.location[0],
        turtle.location[1],
        turtle.location[2] + base_dims[2] + a)
    v3 = (
        turtle.location[0],
        turtle.location[1] + base_dims[1],
        turtle.location[2] + base_dims[2] + a)

    norm = geometry.normal((v1, v2, v3))

    plane = (
        turtle.location[0] + base_dims[0] - margin,
        turtle.location[1],
        turtle.location[2] + base_dims[2])

    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=margin / 4, plane_co=plane, plane_no=norm)

    # create a temporary bmesh for gable ends to select verts inside and create vert groups
    gable_bm = bmesh.new()
    gable_base_dims = base_dims
    gable_base_dims[0] = base_dims[0] - margin
    gable_base_dims[2] = base_dims[2] - margin / 2
    gable_b = gable_base_dims[0]
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
    # assign_verts_to_group(front_verts, obj, deform_groups, "Gable Front")

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
    #assign_verts_to_group(back_verts, obj, deform_groups, "Gable Back")

    bm_deselect_all(bm)
    turtle.location = draw_origin

    # Left side
    left_verts = select_verts_in_bounds(
        lbound=(
            turtle.location[0] - margin,
            turtle.location[1],
            turtle.location[2] + margin),
        ubound=(
            peak_loc[0],
            peak_loc[1] + base_dims[1],
            peak_loc[2] - margin),
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

    verts = bottom_verts + left_verts + right_verts + front_verts + back_verts
    top_verts = [v for v in bm.verts if v not in verts]
    assign_verts_to_group(top_verts, obj, deform_groups, "Top")

    # Additional filter for gables
    verts = left_verts + right_verts + bottom_verts
    front_verts = [v for v in bm.verts if v in front_verts and v not in verts]
    assign_verts_to_group(front_verts, obj, deform_groups, "Gable Front")
    back_verts = [v for v in bm.verts if v in back_verts and v not in verts]
    assign_verts_to_group(back_verts, obj, deform_groups, "Gable Back")

    # finalise turtle and release bmesh
    turtle.location = (0, 0, 0)
    finalise_turtle(bm, obj)

    return obj


def spawn_openlock_base_slot_cutter(base, tile_props, roof_props, offset=0.236):
    """Spawn an openlock base slot cutter into scene and positions it correctly.

    Args:
        base (bpy.types.Object): base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.type.Object: slot cutter
    """
    mode('OBJECT')

    base_location = base.location.copy()
    base_dims = base.dimensions.copy()

    # correct for wall inset distance
    if roof_props.inset_x_neg:
        base_dims[0] = base_dims[0] + roof_props.inset_dist
    if roof_props.inset_x_pos:
        base_dims[0] = base_dims[0] + roof_props.inset_dist
    if roof_props.inset_y_neg:
        base_dims[1] = base_dims[1] + roof_props.inset_dist
    if roof_props.inset_y_pos:
        base_dims[1] = base_dims[1] + roof_props.inset_dist

    # one sided base socket
    if base_dims[0] <= 1 or base_dims[1] <= 1:
        # work out bool size X from base size, y and z are constants.
        bool_size = [
            base_dims[0] - (offset * 2),
            0.155,
            0.25]

        cutter = draw_cuboid(bool_size)
        cutter.name = 'Base Slot.' + tile_props.tile_name + ".slot_cutter"

        diff = base_dims[0] - bool_size[0]

        cutter.location = (
            base_location[0] + diff / 2,
            base_location[1] + offset,
            base_location[2] - 0.001)

        ctx = {
            'object': cutter,
            'active_object': cutter,
            'selected_objects': [cutter]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        return cutter

    # 4 sided base socket
    else:
        preferences = get_prefs()
        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes",
            "booleans",
            "rect_floor_slot_cutter.blend")

        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'corner_xneg_yneg',
                'corner_xneg_ypos',
                'corner_xpos_yneg',
                'corner_xpos_ypos',
                'slot_cutter_a',
                'slot_cutter_b',
                'slot_cutter_c',
                'base_slot_cutter_final']

        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)

        for obj in data_to.objects:
            # obj.hide_set(True)
            obj.hide_viewport = True

        cutter_a = data_to.objects[4]
        cutter_b = data_to.objects[5]
        cutter_c = data_to.objects[6]
        cutter_d = data_to.objects[7]

        cutter_d.name = 'Base Slot Cutter.' + tile_props.tile_name

        a_array = cutter_a.modifiers['Array']
        a_array.fit_length = base_dims[1] - 1.014

        b_array = cutter_b.modifiers['Array']
        b_array.fit_length = base_dims[0] - 1.014

        c_array = cutter_c.modifiers['Array']
        c_array.fit_length = base_dims[0] - 1.014

        d_array = cutter_d.modifiers['Array']
        d_array.fit_length = base_dims[1] - 1.014

        cutter_d.location = (
            base_location[0] + 0.24,
            base_location[1] + 0.24,
            base_location[2] + 0.24)

        return cutter_d

def draw_shed_roof_top(context, margin=0.001):
    """Draw a shed type roof top.

    Args:
        context (bpy.context): context
        margin (float, optional): Margin around textured area. Defaults to 0.001.
    """
    #  B
    #  |\
    # a| \c
    #  |__\A
    #  C b |
    #  |___|

    turtle = context.scene.cursor
    tile = context.collection
    tile_props = tile.mt_tile_props
    roof_tile_props = tile.mt_roof_tile_props

    base_dims = [s for s in tile_props.base_size]

    # correct for inset (difference between standard base width and wall width) to take into account
    # displacement materials
    '''
    if roof_tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    '''
    if roof_tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist
    if roof_tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] - roof_tile_props.inset_dist

    # calculate triangle
    C = 90
    A = roof_tile_props.roof_pitch
    B = 180 - C - A
    b = base_dims[0]
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
    # recalculate triangle to take this into account
    #  B
    #  |\
    # a| \c
    #  |__\A
    #  C b | ▲ side eaves distance
    #  |___| ▼

    a = base_tri['a'] + roof_tile_props.side_eaves
    C = 90
    A = roof_tile_props.roof_pitch
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
    B = roof_tile_props.roof_pitch / 2
    A = 180 - 90 - B
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

    # calculate size of eave end triangle based on roof thickness
    C = 90
    A = roof_tile_props.roof_pitch
    B = 180 - C - A
    a = roof_tile_props.roof_thickness
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
    A = roof_tile_props.roof_pitch
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
    '''
    if roof_tile_props.inset_x_neg:
        ri(bm, roof_tile_props.inset_dist)
    '''
    if roof_tile_props.inset_y_pos:
        fd(bm, roof_tile_props.inset_dist)

    # draw gable end edges
    bk(bm, roof_tile_props.end_eaves_neg)
    ri(bm, inner_tri['b'])
    up(bm, base_dims[2] - roof_tile_props.side_eaves)

    draw_origin = turtle.location.copy()
    pd(bm)

    # vert 0
    add_vert(bm)
    ri(bm, eave_end_tri['c'])
    # vert 1
    ptu(90)
    ylf(90 - outer_tri['A'])
    fd(bm, outer_tri['c'])
    apex_loc = turtle.location.copy()
    # vert 2
    pu(bm)
    # vert 3
    turtle.location=draw_origin
    fd(bm, inner_tri['c'])
    pd(bm)
    add_vert(bm)
    # vert 4
    turtle.location=(0, 0, 0)
    turtle.rotation_euler=(0, 0, 0)

    # create gable end face
    bmesh.ops.contextual_create(bm, geom=bm.verts, mat_nr=0, use_smooth=False)

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
        dist = margin / 4,
        plane_co=plane,
        plane_no = (0, 0, 1))

    # extrude along y
    bm.select_mode = {'FACE'}
    bm_select_all(bm)

    fd(bm, margin, del_original=False)
    subdiv_y_dist = (base_dims[1] - (margin * 2) + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos) / (subdivs[1] - 1)

    i = 1
    while i < subdivs[1]:
        fd(bm, subdiv_y_dist, del_original=True)
        i += 1
    fd(bm, margin, del_original=True)
    bm_deselect_all(bm)

    # create bmesh for selecting top of roof
    top_bm = bmesh.new()
    turtle.location = draw_origin
    top_bm.select_mode = {'VERT'}
    ri(top_bm, eave_end_tri['c'])
    dn(top_bm, margin)
    bk(top_bm, margin)
    ptu(90)
    ylf(90 - outer_tri['A'])
    pd(top_bm)
    add_vert(top_bm)
    fd(top_bm, outer_tri['c'] + margin * 4)
    yri(90)
    top_bm.select_mode = {'EDGE'}
    bm_select_all(top_bm)
    fd(top_bm, margin * 4)
    top_bm.select_mode = {'FACE'}
    turtle.rotation_euler = (0, 0, 0)
    bm_select_all(top_bm)
    fd(top_bm, base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos + margin * 4, False)
    bmesh.ops.recalc_face_normals(top_bm, faces=top_bm.faces)

    # select all points inside top_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, top_bm)

    for vert, select in zip(bm.verts, to_select):

        if vert.co[2] > draw_origin[2] + margin / 4 and \
            vert.co[1] > draw_origin[1] + margin / 4 and \
                vert.co[1] < draw_origin[1] + base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos - (margin / 4):
                vert.select = select
        '''
        if vert.co[0] > base_dims[0] - margin and \
            vert.co[2] > draw_origin[2] + margin / 4 and \
                vert.co[1] > draw_origin[1] + margin / 4 and \
                    vert.co[1] < draw_origin[1] + base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos - (margin / 4):
                    vert.select = select
        '''

    right_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')
    bm_deselect_all(bm)

    # free selection bmesh
    top_bm.free()

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj