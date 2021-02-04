import os
import copy
from math import radians, degrees, tan, sqrt, sin, cos, floor
import bmesh
from mathutils import Vector, kdtree, geometry
import bpy

from bpy.app.handlers import persistent

from bpy.types import Operator, Panel
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)

from .. lib.utils.utils import mode, get_all_subclasses

from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

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

from bpy.types import PropertyGroup

from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty)

from ..enums.enums import (
    roof_types)


class MT_PT_Roof_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Roof_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "ROOF"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        roof_props = scene.mt_roof_scene_props

        layout = self.layout

        layout.label(text="Blueprints")

        layout.prop(roof_props, 'roof_type', text="Roof Type")

        layout.label(text="Socket Types")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint', text="Gable")


        layout.label(text="Roof Footprint")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')

        layout.label(text="Roof Properties")
        layout.prop(scene_props, 'base_z', text="Base Height")
        layout.prop(roof_props, 'roof_pitch', text="Roof Pitch")
        layout.prop(roof_props, 'end_eaves_pos', text="Positive End Eaves")
        layout.prop(roof_props, 'end_eaves_neg', text="Negative End Eaves")
        layout.prop(roof_props, 'side_eaves', text="Side Eaves")
        layout.prop(scene_props, 'subdivision_density', text="Subdivision Density")

        layout.label(text="Wall Inset Correction")
        layout.prop(roof_props, 'inset_dist', text="Inset Distance")
        row = layout.row()
        row.prop(roof_props, 'inset_x_neg', text="X Neg")
        row.prop(roof_props, 'inset_x_pos', text="X Pos")
        row.prop(roof_props, 'inset_y_neg', text="Y Neg")
        row.prop(roof_props, 'inset_y_pos', text="Y Pos")

        layout.operator('scene.reset_tile_defaults')

def initialise_roof_creator(context):
    scene_props = context.scene.mt_scene_props
    roof_scene_props = context.scene.mt_roof_scene_props

    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    create_collection('Roofs', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Roofs'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    roof_tile_props = tile_collection.mt_roof_tile_props

    create_common_tile_props(scene_props, tile_props, tile_collection)

    roof_tile_props.is_roof = True
    roof_tile_props.roof_type = roof_scene_props.roof_type
    roof_tile_props.roof_pitch = roof_scene_props.roof_pitch
    roof_tile_props.end_eaves_pos = roof_scene_props.end_eaves_pos
    roof_tile_props.end_eaves_neg = roof_scene_props.end_eaves_neg
    roof_tile_props.side_eaves = roof_scene_props.side_eaves
    roof_tile_props.roof_thickness = roof_scene_props.roof_thickness
    roof_tile_props.inset_dist = roof_scene_props.inset_dist
    roof_tile_props.inset_x_neg = roof_scene_props.inset_x_neg
    roof_tile_props.inset_x_pos = roof_scene_props.inset_x_pos
    roof_tile_props.inset_y_neg = roof_scene_props.inset_y_neg
    roof_tile_props.inset_y_pos = roof_scene_props.inset_y_pos

    tile_props.tile_type = 'ROOF'

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.subdivision_density = scene_props.subdivision_density
    tile_props.displacement_thickness = scene_props.displacement_thickness

    return cursor_orig_loc, cursor_orig_rot

class MT_OT_Make_Roof(MT_Tile_Generator, Operator):
    """Operator. Generates a roof tile."""

    bl_idname = "object.make_roof"
    bl_label = "Roof"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "ROOF"

    def execute(self, context):
        """Execute the Operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        gable_blueprint = scene_props.main_part_blueprint

        cursor_orig_loc, cursor_orig_rot = initialise_roof_creator(
            context)

        subclasses = get_all_subclasses(MT_Tile_Generator)

        base = spawn_prefab(context, subclasses, base_blueprint, 'ROOF_BASE')
        roof = spawn_prefab(context, subclasses, base_blueprint, 'ROOF_TOP')

        finalise_tile(base, roof, cursor_orig_loc, cursor_orig_rot)

        return {'FINISHED'}


class MT_OT_Make_Openlock_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof Base."""

    bl_idname = "object.make_openlock_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        base = spawn_base(context)
        textured_vertex_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back']
        convert_to_displacement_core(
            base,
            textured_vertex_groups)

        return{'FINISHED'}


class MT_OT_Make_Openlock_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock Roof Top."""

    bl_idname = "object.make_openlock_roof_top"
    bl_label = "Roof Top"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        roof = spawn_roof(context)
        textured_vertex_groups = ['Left', 'Right']
        convert_to_displacement_core(
            roof,
            textured_vertex_groups)
        return{'FINISHED'}

def spawn_roof(context):
    tile = context.collection
    tile_props = tile.mt_tile_props

    roof = draw_apex_roof_top(context)
    roof.name = tile_props.tile_name + '.roof'
    obj_props = roof.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': roof,
        'active_object': roof,
        'selected_objects': [roof],
        'selected_editable_objects': [roof]}

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    return roof

class MT_OT_Make_Plain_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof Base."""

    bl_idname = "object.make_plain_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        base = spawn_base(context)
        textured_vertex_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back']
        convert_to_displacement_core(
            base,
            textured_vertex_groups)
        return{'FINISHED'}

def spawn_base(context):
    tile = context.collection
    tile_props = tile.mt_tile_props

    base = draw_apex_base(context, margin=0.001)
    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base],
        'selected_editable_objects': [base]}

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    return base


def draw_apex_roof_top(context, margin=0.001):
    #      B
    #     /|\
    #    / | \c
    #   / a|  \
    #  /___|___\A
    #  |   C b |
    #  |_______|
    #     base

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

    # calculate triangle
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

    # side eaves distance is vertical distance down from C
    #       B
    #       |\
    #     a | \c
    #       |_ \
    #       |_|_\A
    #      C  b

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

    if density == 'LOW':
        x = floor(base_dims[0] * 4)
        y = floor(base_dims[1] * 4)
        z = floor(base_dims[2] * 4)
    elif density == 'MEDIUM':
        x = floor(base_dims[0] * 8)
        y = floor(base_dims[1] * 8)
        z = floor(base_dims[2] * 8)
    elif density == 'HIGH':
        x = floor(base_dims[0] * 16)
        y = floor(base_dims[1] * 16)
        z = floor(base_dims[2] * 16)
    else:
        x = floor(base_dims[0] * 32)
        y = floor(base_dims[1] * 32)
        z = floor(base_dims[2] * 32)

    subdivs = [x, y, z]

    vert_groups = ['Left', 'Right']
    bm, obj = create_turtle('Roof', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # start
    # check to see if we're correcting for wall thickness
    if roof_tile_props.inset_x_neg:
        ri(bm, roof_tile_props.inset_dist)
    if roof_tile_props.inset_y_pos:
        fd(bm, roof_tile_props.inset_dist)

    # draw gable end edges
    draw_origin = turtle.location.copy()

    bk(bm, roof_tile_props.end_eaves_neg)
    ri(bm, base_dims[0] / 2)
    lf(bm, inner_tri['b'])
    up(bm, base_dims[2] - roof_tile_props.side_eaves)

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
    ptu(90)
    ylf(90 - inner_tri['A'])
    # vert 4
    fd(bm, outer_tri['c'])
    bm.verts.ensure_lookup_table()
    apex_loc = bm.verts[-1].co.copy()

    yri(outer_tri['B'] * 2 + 180)
    # vert 5
    fd(bm, outer_tri['c'])
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
    fd(left_bm, base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos + margin * 4, False)
    bmesh.ops.recalc_face_normals(left_bm, faces=left_bm.faces)

    # select all points inside left_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, left_bm, margin / 2, 0.001)

    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] < apex_loc[0] + margin and \
            vert.co[2] > draw_origin[2] + margin / 4 and \
                vert.co[1] > draw_origin[1] + margin / 4 and \
                    vert.co[1] < draw_origin[1] + base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos - (margin / 4):
                    vert.select = select

    left_verts = [v for v in bm.verts if v.select]

    assign_verts_to_group(left_verts, obj, deform_groups, "Left")
    bm_deselect_all(bm)

    # mirror selector mesh
    ret = bmesh.ops.mirror(
        left_bm,
        geom= left_bm.verts[:] + left_bm.edges[:] + left_bm.faces[:],
        merge_dist=0,
        axis='X')

    verts = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]

    for v in left_bm.verts:
        if v not in verts:
            left_bm.verts.remove(v)

    for v in left_bm.verts:
        v.co[0] = v.co[0] + tile_props.base_size[0]
    bmesh.ops.recalc_face_normals(left_bm, faces=left_bm.faces)

    # select all points inside left_bm
    bm_coords = [v.co.to_tuple() for v in bm.verts]
    to_select = points_are_inside_bmesh(bm_coords, left_bm, margin / 2, 0.001)

    for vert, select in zip(bm.verts, to_select):
        if vert.co[0] > apex_loc[0] - margin and \
            vert.co[2] > draw_origin[2] + margin / 4 and \
                vert.co[1] > draw_origin[1] + margin / 4 and \
                    vert.co[1] < draw_origin[1] + base_dims[1] + roof_tile_props.end_eaves_neg + roof_tile_props.end_eaves_pos - (margin / 4):
                    vert.select = select

    right_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(right_verts, obj, deform_groups, "Right")
    bm_deselect_all(bm)

    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def draw_apex_base(context, margin=0.001):
    """Draw an apex style roof base."""
    #      B
    #     /|\
    #    / | \c
    #   / a|  \
    #  /___|___\A
    #  |   C b |
    #  |_______|
    #     base
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
    density = tile_props.subdivision_density

    if density == 'LOW':
        x = floor(base_dims[0] * 4)
        y = floor(base_dims[1] * 4)
        z = floor(base_dims[2] * 4)
    elif density == 'MEDIUM':
        x = floor(base_dims[0] * 8)
        y = floor(base_dims[1] * 8)
        z = floor(base_dims[2] * 8)
    elif density == 'HIGH':
        x = floor(base_dims[0] * 16)
        y = floor(base_dims[1] * 16)
        z = floor(base_dims[2] * 16)
    else:
        x = floor(base_dims[0] * 32)
        y = floor(base_dims[1] * 32)
        z = floor(base_dims[2] * 32)

    subdivs = [x, y, z]

    for index, value in enumerate(subdivs):
        if value == 0:
            subdivs[index] = 1

    vert_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back', 'Bottom', 'Top']
    bm, obj = create_turtle('Base', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    # start

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

    bm.select_mode = {'VERT'}

    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    ptu(90)
    ylf(90 - A)
    fd(bm, c)
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

    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=margin / 4, plane_co=plane, plane_no=norm)

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

    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=margin / 4, plane_co=plane, plane_no=norm)

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
    to_select = points_are_inside_bmesh(bm_coords, gable_bm, margin / 2, 0.001)

    # points_are_inside isn't perfect on low poly meshes so filter out false positives here
    for vert, select in zip(bm.verts, to_select):
        if vert.co[1] < draw_origin[1] + margin / 2:
            vert.select = select
    front_verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(front_verts, obj, deform_groups, "Gable Front")

    bm_deselect_all(bm)

    # Gable Back
    # move gable mesh to other end

    for v in gable_bm.verts:
        v.co[1] = v.co[1] + base_dims[1]

    to_select = points_are_inside_bmesh(bm_coords, gable_bm, margin / 2, 0.001)
    for vert, select in zip(bm.verts, to_select):
        if vert.co[1] > base_dims[1] - margin / 2:
            vert.select = select

    back_verts = [v for v in bm.verts if v.select]
    # Free gable bmesh as we don;t need it any more
    gable_bm.free()
    assign_verts_to_group(back_verts, obj, deform_groups, "Gable Back")
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

    verts = bottom_verts + left_verts + right_verts + front_verts + back_verts
    top_verts = [v for v in bm.verts if v not in verts]
    assign_verts_to_group(top_verts, obj, deform_groups, "Top")

    turtle.location = (0, 0, 0)
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


class MT_OT_Make_Plain_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof Top."""

    bl_idname = "object.make_plain_roof_top"
    bl_label = "Roof Top"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        return{'FINISHED'}


class MT_OT_Make_Empty_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty roof base."""

    bl_idname = "object.make_empty_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}

class MT_OT_Make_Empty_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty roof top."""

    bl_idname = "object.make_empty_roof_top"
    bl_label = "Roof Gable"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        return{'PASS_THROUGH'}

class MT_Roof_Scene_Properties(PropertyGroup):
    # Roof specific
    last_selected: PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object
    )

    roof_type: EnumProperty(
        name="Roof Type",
        items=roof_types,
        default="APEX"
    )

    roof_pitch: FloatProperty(
        name="Roof Pitch",
        default=45,
        step=1,
        min=0
    )

    end_eaves_pos: FloatProperty(
        name="End Eaves Positive",
        default=0.1,
        step=0.1,
        min=0
    )

    end_eaves_neg: FloatProperty(
        name="End Eaves Negative",
        default=0.1,
        step=0.1,
        min=0
    )

    side_eaves: FloatProperty(
        name="Side Eaves",
        default=0.2,
        step=0.1,
        min=0
    )

    roof_thickness: FloatProperty(
        name="Roof Thickness",
        default=0.1,
        step=0.05,
        min=0
    )

    inset_dist: FloatProperty(
        name="Inset Distance",
        description="Distance core is usually inset from the base of a wall",
        default=0.09,
        min=0
    )

    inset_x_neg: BoolProperty(
        name="Inset X Neg",
        default=True)

    inset_x_pos: BoolProperty(
        name="Inset X Pos",
        default=True)

    inset_y_neg: BoolProperty(
        name="Inset Y Neg",
        default=True)

    inset_y_pos: BoolProperty(
        name="Inset Y Pos",
        default=True)

class MT_Roof_Tile_Properties(PropertyGroup):
    # Roof specific
    is_roof: BoolProperty(
        default=False
    )

    roof_type: EnumProperty(
        name="Roof Type",
        items=roof_types,
        default="APEX"
    )

    roof_pitch: FloatProperty(
        name="Roof Pitch",
        default=45,
        step=1,
        min=0
    )

    end_eaves_pos: FloatProperty(
        name="End Eaves Positive",
        default=0.1,
        step=0.1,
        min=0
    )

    end_eaves_neg: FloatProperty(
        name="End Eaves Negative",
        default=0.1,
        step=0.1,
        min=0
    )

    side_eaves: FloatProperty(
        name="Side Eaves",
        default=0.1,
        step=0.1,
        min=0
    )

    roof_thickness: FloatProperty(
        name="Roof Thickness",
        default=0.1,
        step=0.05,
        min=0
    )

    inset_dist: FloatProperty(
        name="Inset Distance",
        description="Distance core is usually inset from the base of a wall",
        default=0.09,
        min=0
    )

    inset_x_neg: BoolProperty(
        name="Inset X Neg",
        default=True)

    inset_x_pos: BoolProperty(
        name="Inset X Pos",
        default=True)

    inset_y_neg: BoolProperty(
        name="Inset Y Neg",
        default=True)

    inset_y_pos: BoolProperty(
        name="Inset Y Pos",
        default=True)

@persistent
def update_mt_roof_scene_props_handler(dummy):
    """Check to see if we have a MakeTile roof object selected and updates mt_roof_scene_props based on its mt_roof_tile_props."""
    context = bpy.context
    obj = context.object

    roof_scene_props = context.scene.mt_roof_scene_props

    try:
        roof_tile_props = bpy.data.collections[obj.mt_object_props.tile_name].mt_roof_tile_props

        if obj != roof_scene_props.last_selected and roof_tile_props.is_roof:
            roof_scene_props.last_selected = obj

            for key, value in roof_tile_props.items():
                for k in roof_scene_props.keys():
                    if k == key:
                        roof_scene_props[k] = value
    except KeyError:
        pass
    except AttributeError:
        pass

bpy.app.handlers.depsgraph_update_post.append(update_mt_roof_scene_props_handler)

def register():
    # Property group that contains properties set in UI
    bpy.types.Scene.mt_roof_scene_props = PointerProperty(
        type=MT_Roof_Scene_Properties)
    bpy.types.Collection.mt_roof_tile_props = PointerProperty(
        type=MT_Roof_Tile_Properties)


def unregister():
    del bpy.types.Collection.mt_roof_tile_props
    del bpy.types.Scene.mt_roof_scene_props
