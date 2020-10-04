import os
from math import (
    radians)
from mathutils.geometry import intersect_line_line
import bpy
import bmesh
from bpy.types import Operator, Panel
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

from . create_tile import (
    convert_to_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props)

from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    select,
    deselect_all,
    activate)
from .. lib.utils.utils import (
    mode,
    get_all_subclasses,
    distance_between_two_points,
    calc_tri)
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from ..lib.bmturtle.helpers import (
    bm_select_all,
    select_verts_in_bounds,
    assign_verts_to_group,
    calculate_corner_wall_triangles)
from ..lib.bmturtle.commands import (
    create_turtle,
    home,
    finalise_turtle,
    add_vert,
    fd,
    pu,
    pd,
    rt,
    lt,
    up,
    dn,
    arc)


class MT_PT_Semi_Circ_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Semi_Circ_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "SEMI_CIRC_FLOOR"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Properties")
        layout.prop(scene_props, 'tile_z', text="Height")
        layout.prop(scene_props, 'base_radius', text="Radius")
        layout.prop(scene_props, 'angle', text="Angle")
        layout.prop(scene_props, 'curve_type', text="Curve Type")

        layout.label(text="Sync Proportions")
        layout.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Native Subdivisions")
        row = layout.row()
        row.prop(scene_props, 'x_native_subdivisions')
        row.prop(scene_props, 'z_native_subdivisions')
        row.prop(scene_props, 'curve_native_subdivisions')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Semi_Circ_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Semi Circular Floor Tile."""

    bl_idname = "object.make_semi_circ_floor"
    bl_label = "Semi Circular Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "SEMI_CIRC_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'SEMI_CIRC_BASE'
        core_type = 'SEMI_CIRC_FLOOR_CORE'

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(
            context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer
        return {'FINISHED'}


class MT_OT_Make_Openlock_Semi_Circ_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK semi circular base."""

    bl_idname = "object.make_openlock_semi_circ_base"
    bl_label = "OpenLOCK Semi-Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Semi_Circ_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain semi circular base."""

    bl_idname = "object.make_plain_semi_circ_base"
    bl_label = "Plain Semi Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Semi_Circular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty semi circular base."""

    bl_idname = "object.make_empty_semi_circ_base"
    bl_label = "Empty Semi Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain semi circular floor core."""

    bl_idname = "object.make_plain_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "SEMI_CIRC_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_floor_cores(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock semi circular floor core."""

    bl_idname = "object.make_openlock_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "SEMI_CIRC_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_floor_cores(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty semi circular floor core."""

    bl_idname = "object.make_empty_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "SEMI_CIRC_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def initialise_floor_creator(context, scene_props):
    """Initialise the floor creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (MakeTile.properties.MT_Scene_Properties): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'SEMI_CIRC_FLOOR'

    tile_props.base_radius = scene_props.base_radius
    tile_props.angle = scene_props.angle
    tile_props.curve_type = scene_props.curve_type

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions
    tile_props.curve_native_subdivisions = scene_props.curve_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    dimensions = {
        'height': tile_props.base_size[2],
        'angle': tile_props.angle,
        'radius': tile_props.base_radius}

    subdivs = {
        'arc': tile_props.curve_native_subdivisions}

    curve_type = tile_props.curve_type

    if curve_type == 'POS':
        base = draw_pos_curved_semi_circ_base(dimensions, subdivs)
    else:
        base = draw_neg_curved_semi_circ_base(dimensions, subdivs)

    ctx = {
        'selected_objects': [base],
        'active_object': base
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn OpenLOCK base into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base
    """
    curve_type = tile_props.curve_type

    dimensions = {
        'height': tile_props.base_size[2],
        'angle': tile_props.angle,
        'radius': tile_props.base_radius,
        'outer_w': 0.236,
        'slot_w': 0.181,
        'slot_h': 0.24}

    subdivs = {
        'arc': tile_props.curve_native_subdivisions}

    base = spawn_plain_base(tile_props)

    base.mt_object_props.geometry_type = 'BASE'
    ctx = {
        'selected_objects': [base],
        'object': base,
        'active_object': base,
        'selected_editable_objects': [base]}

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'

    slot_cutter = None
    if curve_type == 'POS':
        slot_cutter = draw_pos_curved_slot_cutter(dimensions, subdivs)
    else:
        if dimensions['radius'] >= 2:
            slot_cutter = draw_neg_curved_slot_cutter(dimensions)

    if slot_cutter:
        slot_cutter.name = 'Slot.cutter.' + base.name
        set_bool_obj_props(slot_cutter, base, tile_props)
        set_bool_props(slot_cutter, base, 'DIFFERENCE')

    cutters = create_openlock_base_clip_cutters(tile_props)

    for clip_cutter in cutters:
        set_bool_obj_props(clip_cutter, base, tile_props)
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    bpy.context.view_layer.objects.active = base

    return base


def spawn_plain_floor_cores(tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_core(tile_props)
    textured_vertex_groups = ['Top']

    convert_to_displacement_core(
        core,
        textured_vertex_groups)
    return core


def spawn_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    base_size = tile_props.base_size
    curve_type = tile_props.curve_type

    dimensions = {
        'radius': tile_props.base_radius,
        'angle': tile_props.angle,
        'height': tile_props.tile_size[2] - tile_props.base_size[2]}

    subdivs = {
        'sides': tile_props.x_native_subdivisions,
        'arc': tile_props.curve_native_subdivisions,
        'z': tile_props.z_native_subdivisions}

    if curve_type == 'POS':
        core = draw_pos_curved_semi_circ_core(dimensions, subdivs)
    else:
        core = draw_neg_curved_semi_circ_core(dimensions, subdivs)

    core.location[2] = core.location[2] + base_size[2]
    core.name = tile_props.tile_name + '.core'

    ctx = {
        'selected_editable_objects': [core],
        'selected_objects': [core],
        'object': core,
        'active_object': core
    }

    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    return core


def create_openlock_base_clip_cutters(tile_props):
    """Generate base clip cutters for semi circular tiles.

    Args:
        tile_props (bpy.types.MT_Tile_Properties): tile properties

    Returns:
        list[bpy.types.Object]: Base cutters
    """
    mode('OBJECT')

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()

    radius = tile_props.base_radius
    angle = tile_props.angle
    curve_type = tile_props.curve_type
    cutters = []
    if curve_type == 'NEG':
        radius = radius / 2

    if radius >= 1:
        preferences = get_prefs()
        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes", "booleans", "openlock.blend")

        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'openlock.wall.base.cutter.clip',
                'openlock.wall.base.cutter.clip.cap.start',
                'openlock.wall.base.cutter.clip.cap.end']

        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)

        clip_cutter_1 = data_to.objects[0]
        clip_cutter_1.name = "Clip Cutter 1"
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        cutter_start_cap.hide_viewport = True
        cutter_end_cap.hide_viewport = True

        array_mod = clip_cutter_1.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'

        if angle >= 90:
            clip_cutter_1.location = (
                cursor_orig_loc[0] + 0.5,
                cursor_orig_loc[1] + 0.25,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1
        else:
            clip_cutter_1.location = (
                cursor_orig_loc[0] + 1,
                cursor_orig_loc[1] + 0.25,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1.5

        deselect_all()
        select(clip_cutter_1.name)

        bpy.ops.transform.rotate(
            value=(radians(angle - 90)),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=cursor_orig_loc)

        cutters.append(clip_cutter_1)
        # cutter 2
        clip_cutter_2 = clip_cutter_1.copy()
        clip_cutter_2.name = "Clip Cutter 2"
        add_object_to_collection(clip_cutter_2, tile_props.tile_name)

        array_mod = clip_cutter_2.modifiers['Array']

        if angle >= 90:
            clip_cutter_2.location = (
                cursor_orig_loc[0] + 0.25,
                cursor_orig_loc[1] + radius - 0.5,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1
        else:
            clip_cutter_2.location = (
                cursor_orig_loc[0] + 0.25,
                cursor_orig_loc[1] + radius - 0.5,
                cursor_orig_loc[2]
            )
            array_mod.fit_length = radius - 1.5

        clip_cutter_2.rotation_euler = (0, 0, radians(-90))
        cutters.append(clip_cutter_2)

        deselect_all()

    if tile_props.curve_type == 'POS':
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip_single']
        clip_cutter_3 = data_to.objects[0]
        clip_cutter_3.name = "Clip Cutter 3"
        add_object_to_collection(clip_cutter_3, tile_props.tile_name)

        deselect_all()
        select(clip_cutter_3.name)

        clip_cutter_3.rotation_euler = (0, 0, radians(180))
        clip_cutter_3.location[1] = cursor_orig_loc[1] + radius - 0.25
        bpy.ops.transform.rotate(
            value=(radians(angle / 2)),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=cursor_orig_loc)

        cutters.append(clip_cutter_3)

    for cutter in cutters:
        props = cutter.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name
        props.geometry_type = 'CUTTER'

    return cutters


def draw_pos_curved_semi_circ_base(dimensions, subdivs):
    """Return a positively curved semi circular base.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: base
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    bm, obj = create_turtle('base')
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)
    fd(bm, radius)
    pu(bm)
    home(obj)
    pd(bm)

    # we only draw part of the arc and then join the end to the final side later
    # we do this because there's always a difference in the location of the final
    # vert  of the arc and the final vert of the side it needs to connect to so
    # merge by distance doesn't work.
    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)
    arc(bm, radius, part_angle, subdivs['arc'] - 1)
    pd(bm)
    add_vert(bm)
    rt(angle)
    fd(bm, radius)
    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)

    # join final vert of arc with side
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bm.edges)
    pd(bm)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)
    pu(bm)
    home(obj)

    finalise_turtle(bm, obj)
    return obj


def draw_neg_curved_semi_circ_base(dimensions, subdivs):
    """Return a negatively curved semi circular base.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: base
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    # calculate a triangle that is the mirror of the one formed by legs b an c
    triangle = calc_tri(angle, radius, radius)

    bm, obj = create_turtle('base')
    verts = bm.verts
    bm.select_mode = {'VERT'}
    pd(bm)
    add_vert(bm)

    fd(bm, radius)
    pu(bm)
    home(obj)
    pd(bm)
    rt(angle)
    add_vert(bm)
    fd(bm, radius)
    pu(bm)
    lt(180 - triangle['C'] * 2)
    fd(bm, radius)
    lt(180)

    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)
    pu(bm)
    home(obj)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.01)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, height, False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_pos_curved_semi_circ_core(dimensions, subdivs, margin=0.001):
    """Return a positively curved semi circular core.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{
            sides: float,
            arc: float}): subdivisions
        margin (float): margin between texturewd and blank area

    Returns:
        bpy.type.Object: core
    """

    #   B
    #   |\
    # c |   \ a
    #   |      \
    #   |________ \
    #  A    b    C
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    vert_groups = [
        'Side a',
        'Side b',
        'Side c',
        'Top',
        'Bottom']

    vert_locs = {
        'Side a': [],
        'Side b': [],
        'Side c': [],
        'Top': [],
        'Bottom': []}

    bm, obj = create_turtle('core', vert_groups)
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)

    verts.ensure_lookup_table()
    vert_locs['Side c'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side c'].append(verts[-1].co.copy())
        i += 1

    pu(bm)
    home(obj)
    pd(bm)

    verts.ensure_lookup_table()
    start_index = verts[-1].index + 1

    # only draw n-1 segments of arc as we will join arc and side together later
    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)

    verts.ensure_lookup_table()
    i = start_index
    while i <= verts[-1].index:
        vert_locs['Side a'].append(verts[i].co.copy())
        i += 1

    pd(bm)
    add_vert(bm)
    rt(angle)

    verts.ensure_lookup_table()
    vert_locs['Side b'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side b'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because or error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=margin / 2)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    # bmesh.ops.grid_fill doesn't work as well as bpy.ops.grid_fill so we use that instead despite
    # it being slower and requiring us to rebuild our bmesh

    bm_select_all(bm)
    bm.select_flush(True)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()

    activate(obj.name)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.fill_grid(span=subdivs['sides'])
    bpy.ops.object.editmode_toggle()

    bm = bmesh.new()
    bm.from_mesh(mesh)

    pd(bm)
    verts = bm.verts
    bottom_verts = [v for v in verts]

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)

    selected_faces = [f for f in bm.faces if f.select]

    bmesh.ops.inset_region(
        bm,
        faces=selected_faces,
        thickness=margin,
        use_boundary=True,
        use_even_offset=True)

    verts.layers.deform.verify()
    deform_groups = verts.layers.deform.active

    side_b_verts = []
    for loc in vert_locs['Side b']:
        side_b_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    side_c_verts = select_verts_in_bounds(
        lbound=obj.location,
        ubound=(obj.location[0], obj.location[1] + radius, obj.location[2] + height),
        buffer=margin / 2,
        bm=bm)

    side_a_verts = []
    for loc in vert_locs['Side a']:
        side_a_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    # verts not to include in top
    vert_list = bottom_verts + side_a_verts + side_b_verts + side_c_verts

    # assign verts to groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')
    assign_verts_to_group(side_a_verts, obj, deform_groups, 'Side a')
    assign_verts_to_group(side_c_verts, obj, deform_groups, 'Side c')
    assign_verts_to_group(side_b_verts, obj, deform_groups, 'Side b')
    assign_verts_to_group(
        [v for v in bm.verts if v not in vert_list],
        obj,
        deform_groups,
        'Top')

    finalise_turtle(bm, obj)
    return obj


def draw_neg_curved_semi_circ_core(dimensions, subdivs, margin=0.001):
    """Return a negatively curved semi circular core.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{
            sides: float,
            arc: float}): subdivisions
        margin (float): margin between texturewd and blank area

    Returns:
        bpy.type.Object: core
    """

    #   B
    #   |\
    # c |   \ a
    #   |      \
    #   |________ \
    #  A    b    C
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    vert_groups = [
        'Side a',
        'Side b',
        'Side c',
        'Top',
        'Bottom']

    vert_locs = {
        'Side a': [],
        'Side b': [],
        'Side c': [],
        'Top': [],
        'Bottom': []}

    # calculate a triangle that is the mirror of the one formed by legs b an c
    triangle = calc_tri(angle, radius, radius)

    bm, obj = create_turtle('core', vert_groups)
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)

    verts.ensure_lookup_table()
    vert_locs['Side c'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side c'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because of margin of error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    home(obj)
    pd(bm)

    rt(angle)
    add_vert(bm)
    verts.ensure_lookup_table()
    vert_locs['Side b'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side b'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because or error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    lt(180 - triangle['C'] * 2)
    fd(bm, radius)
    lt(180)

    verts.ensure_lookup_table()
    start_index = bm.verts[-1].index + 1

    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)

    verts.ensure_lookup_table()
    i = start_index
    while i <= verts[-1].index:
        vert_locs['Side a'].append(verts[i].co.copy())
        i += 1

    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=margin / 2)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    # we get a glitch on some sizes of cores if we just use triangle fill so we do this instead
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=True, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.beautify_fill(bm, faces=bm.faces, edges=bm.edges)

    bottom_verts = [v for v in bm.verts]

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, height, False)

    selected_faces = [f for f in bm.faces if f.select]

    bmesh.ops.inset_region(
        bm,
        faces=selected_faces,
        thickness=margin,
        use_boundary=True,
        use_even_offset=False)

    verts.layers.deform.verify()
    deform_groups = verts.layers.deform.active

    side_b_verts = []
    for loc in vert_locs['Side b']:
        side_b_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    side_c_verts = select_verts_in_bounds(
        lbound=obj.location,
        ubound=(obj.location[0], obj.location[1] + radius, obj.location[2] + height),
        buffer=margin / 2,
        bm=bm)

    side_a_verts = []
    for loc in vert_locs['Side a']:
        side_a_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    # verts not to include in top
    vert_list = bottom_verts + side_a_verts + side_b_verts + side_c_verts

    # assign verts to groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')
    assign_verts_to_group(side_a_verts, obj, deform_groups, 'Side a')
    assign_verts_to_group(side_c_verts, obj, deform_groups, 'Side c')
    assign_verts_to_group(side_b_verts, obj, deform_groups, 'Side b')
    assign_verts_to_group(
        [v for v in bm.verts if v not in vert_list],
        obj,
        deform_groups,
        'Top')

    finalise_turtle(bm, obj)
    return obj


def draw_pos_curved_slot_cutter(dimensions, subdivs):
    """Return a positively curved base slot cutter.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: slot cutter
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    outer_w = dimensions['outer_w']
    slot_w = dimensions['slot_w']
    slot_h = dimensions['slot_h']

    bm, obj = create_turtle('base')
    verts = bm.verts

    bm.select_mode = {'VERT'}
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    pu(bm)

    # get locs of ends of edges inside and parallel to base outer edges
    rt(angle)
    fd(bm, radius / 2)
    lt(90)
    fd(bm, outer_w)
    lt(90)
    v1 = turtle.location.copy()
    fd(bm, 0.01)
    v2 = turtle.location.copy()

    home(obj)
    fd(bm, radius / 2)
    rt(90)
    fd(bm, outer_w)
    rt(90)
    v3 = turtle.location.copy()
    fd(bm, 0.01)
    v4 = turtle.location.copy()

    # get intersection
    intersection = intersect_line_line(v1, v2, v3, v4)
    intersection = (intersection[0] + intersection[1]) / 2
    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)
    dist = distance_between_two_points(origin, intersection)

    new_radius = radius - dist - outer_w

    # draw outer arc
    arc(bm, new_radius, angle, subdivs['arc'] + 1)

    # draw sides
    add_vert(bm)
    pd(bm)
    fd(bm, new_radius)
    pu(bm)
    turtle.location = intersection
    pd(bm)
    verts.ensure_lookup_table()
    verts[-2].select = True
    rt(angle)
    fd(bm, new_radius)
    pu(bm)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)

    # repeat for inner edge of slot cutter
    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)

    # get locs of ends of edges inside and parallel to base outer edges
    rt(angle)
    fd(bm, radius / 2)
    lt(90)
    fd(bm, slot_w)
    lt(90)
    v1 = turtle.location.copy()
    fd(bm, 0.01)
    v2 = turtle.location.copy()

    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)
    fd(bm, radius / 2)
    rt(90)
    fd(bm, slot_w)
    rt(90)
    v3 = turtle.location.copy()
    fd(bm, 0.01)
    v4 = turtle.location.copy()

    # get intersection
    intersection_2 = intersect_line_line(v1, v2, v3, v4)
    intersection_2 = (intersection_2[0] + intersection_2[1]) / 2
    turtle.location = intersection_2
    turtle.rotation_euler = (0, 0, 0)
    dist = distance_between_two_points(intersection, intersection_2)

    new_radius = new_radius - dist - slot_w

    # draw outer arc
    arc(bm, new_radius, angle, subdivs['arc'] + 1)
    add_vert(bm)
    pd(bm)
    fd(bm, new_radius)
    pu(bm)
    turtle.location = intersection_2
    pd(bm)
    verts.ensure_lookup_table()
    verts[-2].select = True
    rt(angle)
    fd(bm, new_radius)
    pu(bm)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)
    bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, slot_h + 0.001, False)
    pu(bm)
    home(obj)
    obj.location = (obj.location[0], obj.location[1], obj.location[2] - 0.001)
    finalise_turtle(bm, obj)

    return obj


def draw_neg_curved_slot_cutter(dimensions):
    """Return a negatively curved base slot cutter.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions

    Returns:
        bpy.type.Object: slot cutter
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    outer_w = dimensions['outer_w']
    slot_w = dimensions['slot_w']
    slot_h = dimensions['slot_h'] + 0.001

    triangles_1 = calculate_corner_wall_triangles(
        radius,
        radius,
        outer_w,
        angle)

    x_leg = triangles_1['b_adj'] - outer_w
    y_leg = triangles_1['d_adj'] - outer_w

    triangles_2 = calculate_corner_wall_triangles(
        x_leg,
        y_leg,
        slot_w,
        angle)

    bm, obj = create_turtle('slot_cutter')
    bm.select_mode = {'VERT'}

    turtle = bpy.context.scene.cursor
    # move turtle to start
    orig_rot = turtle.rotation_euler.copy()

    pu(bm)
    dn(bm, 0.001)
    rt(angle)
    fd(bm, triangles_1['a_adj'])
    lt(90)
    fd(bm, outer_w)
    lt(90)
    fd(bm, triangles_1['b_adj'])
    turtle.rotation_euler = orig_rot
    turtle_start_loc = turtle.location.copy()
    pd(bm)

    add_vert(bm)
    rt(angle)
    fd(bm, triangles_2['a_adj'] - (radius / 2))
    lt(90)
    fd(bm, slot_w)
    lt(90)
    fd(bm, triangles_2['b_adj'] - (radius / 2))
    pu(bm)
    home(obj)
    turtle.location = turtle_start_loc
    pd(bm)
    add_vert(bm)
    fd(bm, triangles_2['c_adj'] - (radius / 2))
    rt(90)
    fd(bm, slot_w)
    rt(90)
    fd(bm, triangles_2['d_adj'] - (radius / 2))

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, slot_h, False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)
    return obj
