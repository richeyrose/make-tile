import os
from math import radians
import bpy
from bpy.types import Operator, Panel
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

from . create_tile import (
    create_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab)

from .. lib.turtle.scripts.curved_floor import (
    draw_neg_curved_slab,
    draw_pos_curved_slab,
    draw_openlock_pos_curved_base)
from .. lib.turtle.scripts.L_tile import (
    calculate_corner_wall_triangles,
    move_cursor_to_wall_start,
    draw_corner_3D)
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group
)
from .. utils.registration import get_prefs
from .. lib.utils.selection import select, deselect_all, select_by_loc, select_inverse_by_loc
from .. lib.utils.utils import (
    mode,
    get_all_subclasses)
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)


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
        """Check tile_type_new."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type_new == "object.make_semi_circ_floor"
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
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
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
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
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
        scene_props (bpy.types.PropertyGroup.mt_scene_props): maketile scene properties

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
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions
    tile_props.curve_native_subdivisions = scene_props.curve_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    radius = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    angle = tile_props.angle
    height = tile_props.base_size[2]
    curve_type = tile_props.curve_type
    native_subdivisions = (
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions,
        tile_props.curve_native_subdivisions
    )

    if curve_type == 'POS':
        base = draw_pos_curved_slab(radius, segments, angle, height, native_subdivisions)
    else:
        base = draw_neg_curved_slab(radius, segments, angle, height, native_subdivisions)

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
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: base
    """
    length = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    angle = tile_props.angle
    height = tile_props.base_size[2]
    curve_type = tile_props.curve_type
    native_subdivisions = (
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions,
        tile_props.curve_native_subdivisions
    )

    if curve_type == 'POS':
        base = draw_openlock_pos_curved_base(length, segments, angle, height)
        base.mt_object_props.geometry_type = 'BASE'
        ctx = {
            'selected_objects': [base],
            'active_object': base
        }
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    else:
        draw_neg_curved_slab(length, segments, angle, height, native_subdivisions)
        base = bpy.context.object
        base.mt_object_props.geometry_type = 'BASE'
        ctx = {
            'selected_objects': [base],
            'active_object': base
        }
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        if length >= 3:
            slot_cutter = create_openlock_neg_curve_base_cutters(tile_props)
            slot_cutter.parent = base
            slot_cutter.display_type = 'BOUNDS'
            slot_cutter.hide_viewport = True
            cutter_bool = base.modifiers.new('Slot Cutter', 'BOOLEAN')
            cutter_bool.operation = 'DIFFERENCE'
            cutter_bool.object = slot_cutter

    cutters = create_openlock_base_clip_cutters(tile_props)

    for clip_cutter in cutters:
        matrixcopy = clip_cutter.matrix_world.copy()
        clip_cutter.parent = base
        clip_cutter.matrix_world = matrixcopy
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'
    bpy.context.view_layer.objects.active = base

    return base


def spawn_plain_floor_cores(base, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_core(tile_props)
    textured_vertex_groups = ['Top']

    core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    return core


def spawn_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: core
    """
    base_size = tile_props.base_size
    radius = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    angle = tile_props.angle
    height = tile_props.tile_size[2] - base_size[2]
    curve_type = tile_props.curve_type
    native_subdivisions = (
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions,
        tile_props.curve_native_subdivisions
    )

    if curve_type == 'POS':
        core = draw_pos_curved_slab(
            radius,
            segments,
            angle,
            height,
            native_subdivisions)
        positively_curved_floor_to_vert_groups(
            core,
            height,
            radius)
    else:
        core, vert_locs = draw_neg_curved_slab(
            radius,
            segments,
            angle,
            height,
            native_subdivisions,
            return_vert_locs=True)
        neg_curved_floor_to_vert_groups(
            core,
            height,
            radius,
            vert_locs
        )

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


def create_openlock_neg_curve_base_cutters(tile_props):
    """Generate base cutters for negatively curved tiles.

    Args:
        tile_props (bpy.types.MT_Tile_Properties): tile properties

    Returns:
        list[bpy.types.Object]: Base cutters
    """
    length = tile_props.base_radius / 2
    angle = tile_props.angle
    face_dist = 0.233
    slot_width = 0.197
    slot_height = 0.25
    end_dist = 0.236  # distance of slot from base end

    cutter_triangles_1 = calculate_corner_wall_triangles(
        length,
        length,
        face_dist,
        angle)

    # reuse method we use to work out where to start our corner wall
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

    cutter = draw_corner_3D(
        cutter_triangles_2,
        angle,
        slot_width,
        slot_height
    )

    cutter.name = tile_props.tile_name + '.base.cutter'

    props = cutter.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'CUTTER'
    return cutter


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
        clip_cutter_1.name = "cutter_1"
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
            value=(radians(-angle + 90)),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=cursor_orig_loc)

        cutters.append(clip_cutter_1)
        # cutter 2
        clip_cutter_2 = clip_cutter_1.copy()
        clip_cutter_2.name = "cutter_2"
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
        clip_cutter_3.name = "cutter_3"
        add_object_to_collection(clip_cutter_3, tile_props.tile_name)

        deselect_all()
        select(clip_cutter_3.name)

        clip_cutter_3.rotation_euler = (0, 0, radians(180))
        clip_cutter_3.location[1] = cursor_orig_loc[1] + radius - 0.25
        bpy.ops.transform.rotate(
            value=(radians(-angle / 2)),
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


def neg_curved_floor_to_vert_groups(obj, height, side_length, vert_locs):
    """Create vertex groups for negatively curved semi circular floors.

    Args:
        obj (bpy.types.Object): Floor core
        height (float): height
        side_length (float): side length
        vert_locs (dict): vertex locations
    """
    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]
    }

    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')
    select(obj.name)
    mode('EDIT')
    deselect_all()

    select_by_loc(
        lbound=(obj.location),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2]),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    for key, value in vert_locs.items():
        if key == 'side_a':
            for v in value:
                select_by_loc(
                    lbound=v,
                    ubound=(v[0], v[1], v[2] + height),
                    select_mode='VERT',
                    coords='GLOBAL',
                    additive=True,
                    buffer=0.0001
                )

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        additive=True,
        coords='GLOBAL'
    )

    bpy.ops.object.vertex_group_set_active(ctx, group='Side a')
    bpy.ops.object.vertex_group_assign(ctx)
    deselect_all()

    # side b
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )

    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    mode('OBJECT')

    # get verts in side groups
    side_groups = ['Side a', 'Side b', 'Side c']
    side_vert_indices = []

    for group in side_groups:
        verts = get_vert_indexes_in_vert_group(group, bpy.context.object)
        side_vert_indices.extend(verts)

    remove_verts_from_group('Top', bpy.context.object, side_vert_indices)


def positively_curved_floor_to_vert_groups(obj, height, side_length):
    """Create vertex groups for positively curved semi circular floors.

    Args:
        obj (bpy.types.Object): Floor core
        height (float): height
        side_length (float): side length
        vert_locs (dict): vertex locations
    """
    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')
    select(obj.name)
    mode('EDIT')

    deselect_all()
    select_by_loc(
        lbound=(obj.location),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2]),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_inverse_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side a')
    bpy.ops.object.vertex_group_assign()

    mode('OBJECT')
