import os
from math import radians
import bpy
from bpy.types import Panel, Operator
import bmesh
from mathutils import Vector
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group)
from .. lib.utils.utils import mode, vectors_are_close, get_all_subclasses
from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    deselect_all,
    select)
from ..lib.bmturtle.scripts import (
    draw_corner_3D as draw_corner_3D_bm,
    draw_corner_floor_core,
    draw_corner_wall_core)
from .. lib.turtle.scripts.L_Tile import (
    draw_corner_3D,
    calculate_corner_wall_triangles,
    move_cursor_to_wall_start)
from . create_tile import (
    create_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_props,
    set_bool_obj_props,
    load_openlock_top_peg)
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)


class MT_PT_L_Tile_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_L_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type in ["L_WALL", "L_FLOOR"]
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
        layout.prop(scene_props, 'leg_1_len')
        layout.prop(scene_props, 'leg_2_len')
        layout.prop(scene_props, 'angle')
        layout.prop(scene_props, 'tile_z', text="Height")

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        layout.prop(scene_props, 'z_proportionate_scale', text="Height")
        layout.prop(scene_props, 'y_proportionate_scale', text="Width")

        layout.label(text="Base Properties")
        layout.prop(scene_props, "base_z", text="Height")
        layout.prop(scene_props, "base_y", text="Width")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_L_Wall_Tile(MT_Tile_Generator, Operator):
    """Create an L Wall Tile."""

    bl_idname = "object.make_l_wall_tile"
    bl_label = "L Wall"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "L_WALL"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'L_BASE'
        core_type = 'L_WALL_CORE'

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_wall_creator(
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


class MT_OT_Make_L_Floor_Tile(MT_Tile_Generator, Operator):
    """Create an L Floor Tile."""

    bl_idname = "object.make_l_floor_tile"
    bl_label = "L Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "L_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'L_BASE'
        core_type = 'L_FLOOR_CORE'

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


class MT_OT_Make_Openlock_L_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK L base."""

    bl_idname = "object.make_openlock_l_base"
    bl_label = "OpenLOCK L Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "L_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_L_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain L base."""

    bl_idname = "object.make_plain_l_base"
    bl_label = "Plain L Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "L_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_L_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty L base."""

    bl_idname = "object.make_empty_l_base"
    bl_label = "Empty L Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "L_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_L_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain L wall core."""

    bl_idname = "object.make_plain_l_wall_core"
    bl_label = "L Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "L_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_wall_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_L_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock L wall core."""

    bl_idname = "object.make_openlock_l_wall_core"
    bl_label = "L Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "L_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_openlock_wall_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_L_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty L wall core."""

    bl_idname = "object.make_empty_l_wall_core"
    bl_label = "L Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "L_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Plain_L_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain L wall core."""

    bl_idname = "object.make_plain_l_floor_core"
    bl_label = "L Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "L_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_L_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock L floor core."""

    bl_idname = "object.make_openlock_l_floor_core"
    bl_label = "L Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "L_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_L_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty L floor core."""

    bl_idname = "object.make_empty_l_floor_core"
    bl_label = "L Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "L_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def initialise_wall_creator(context, scene_props):
    """Initialise the wall creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (MakeTile.properties.MT_Scene_Properties): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Walls', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Walls'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'L_WALL'

    tile_props.leg_1_len = scene_props.leg_1_len
    tile_props.leg_2_len = scene_props.leg_2_len
    tile_props.angle = scene_props.angle

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.leg_1_native_subdivisions = scene_props.leg_1_native_subdivisions
    tile_props.leg_2_native_subdivisions = scene_props.leg_2_native_subdivisions
    tile_props.width_native_subdivisions = scene_props.width_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


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
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'L_FLOOR'

    tile_props.leg_1_len = scene_props.leg_1_len
    tile_props.leg_2_len = scene_props.leg_2_len
    tile_props.angle = scene_props.angle

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.leg_1_native_subdivisions = scene_props.leg_1_native_subdivisions
    tile_props.leg_2_native_subdivisions = scene_props.leg_2_native_subdivisions
    tile_props.width_native_subdivisions = scene_props.width_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_wall_cores(base, tile_props):
    """Spawn plain wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    preview_core = spawn_wall_core(tile_props)
    textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 2 Outer', 'Leg 2 Inner']
    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    return preview_core


def spawn_plain_floor_cores(base, tile_props):
    """Spawn plain floor cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    textured_vertex_groups = ['Leg 1 Top', 'Leg 2 Top']
    preview_core = spawn_floor_core(tile_props)

    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    return preview_core


def spawn_floor_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    base_thickness = tile_props.base_size[1]
    core_thickness = tile_props.tile_size[1]
    base_height = tile_props.base_size[2]
    floor_height = tile_props.tile_size[2]
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle
    native_subdivisions = (
        tile_props.leg_1_native_subdivisions,
        tile_props.leg_2_native_subdivisions,
        tile_props.width_native_subdivisions,
        tile_props.z_native_subdivisions)
    thickness_diff = base_thickness - core_thickness

    # first work out where we're going to start drawing our wall
    # from, taking into account the difference in thickness
    # between the base and wall and how long our legs will be
    core_triangles_1 = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness_diff / 2,
        angle)

    core_x_leg = core_triangles_1['b_adj']
    core_y_leg = core_triangles_1['d_adj']

    # work out dimensions of core
    core_triangles_2 = calculate_corner_wall_triangles(
        core_x_leg,
        core_y_leg,
        core_thickness,
        angle)

    core = draw_corner_floor_core(
        core_triangles_1,
        core_triangles_2,
        angle,
        core_thickness,
        thickness_diff,
        base_height,
        floor_height - base_height,
        native_subdivisions)

    core.name = tile_props.tile_name + '.core'
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core],
        'selected_editable_objects': [core]}

    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    return core


def spawn_openlock_wall_cores(base, tile_props):
    """Spawn openlock wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """

    preview_core = spawn_wall_core(tile_props)
    textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 2 Outer', 'Leg 2 Inner']
    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)

    cutters = spawn_openlock_wall_cutters(preview_core, tile_props)

    cores = [preview_core, displacement_core]

    if tile_props.leg_1_len >= 1 or tile_props.leg_2_len >= 1:
        top_pegs = spawn_openlock_top_pegs(
            preview_core,
            tile_props)

        for pegs in top_pegs:
            set_bool_obj_props(pegs, base, tile_props)
            for core in cores:
                set_bool_props(pegs, core, 'UNION')

    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props)
        for core in cores:
            set_bool_props(cutter, core, 'DIFFERENCE')

    displacement_core.hide_viewport = True
    bpy.context.scene.cursor.location = (0, 0, 0)

    return preview_core


def spawn_openlock_top_pegs(core, tile_props):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        core (bpy.types.Object): tile core
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """

    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    cursor = bpy.context.scene.cursor
    peg = load_openlock_top_peg(tile_props)

    core_location = core.location.copy()
    pegs = []

    # leg 1
    if leg_1_len >= 1:
        peg.location = (
            core_location[0] + 0.756,
            core_location[1] + (base_size[1] / 2) + 0.08,
            core_location[2] + tile_size[2])

        if leg_1_len >= 2:
            array_mod = peg.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[0] = 0.505
            array_mod.fit_type = 'FIXED_COUNT'
            array_mod.count = 2

        if leg_1_len >= 4:
            array_mod = peg.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[0] = 2.017
            array_mod.fit_type = 'FIT_LENGTH'
            array_mod.fit_length = leg_1_len - 1.3

        ctx = {
            'object': peg,
            'active_object': peg,
            'selected_objects': [peg]
        }
        bpy.ops.transform.rotate(
            ctx,
            value=radians(tile_props.angle - 90),
            orient_axis='Z',
            center_override=cursor.location)
        pegs.append(peg)

    # leg 2
    if leg_2_len >= 1:
        peg_2 = load_openlock_top_peg(tile_props)
        peg_2.rotation_euler[2] = radians(-90)
        ctx = {
            'object': peg_2,
            'active_object': peg_2,
            'selected_objects': [peg_2],
            'selectable_objects': [peg_2],
            'selected_editable_objects': [peg_2]
        }

        bpy.ops.object.transform_apply(
            ctx,
            location=False,
            rotation=True,
            scale=False,
            properties=True)

        peg_2.location = (
            core_location[0] + (base_size[1] / 2) + 0.08,
            core_location[1] + 0.756,
            core_location[2] + tile_size[2])

        if leg_2_len >= 2:
            array_mod = peg_2.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 0.505
            array_mod.fit_type = 'FIXED_COUNT'
            array_mod.count = 2

        if leg_2_len >= 4:
            array_mod = peg_2.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 2.017
            array_mod.fit_type = 'FIT_LENGTH'
            array_mod.fit_length = leg_2_len - 1.3

        pegs.append(peg_2)
    return pegs


def spawn_openlock_wall_cutters(core, tile_props):
    """Create the cutters for the wall and position them correctly.

    Args:
        core (bpy.types.Object): tile core
        tile_props (bpy.types.MT_Tile_Props): tile propertis

    Returns:
        list[bpy.types.Object]: list of cutters
    """
    preferences = get_prefs()

    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    core_location = core.location.copy()

    cutters = []
    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    left_cutter_bottom.name = 'Leg 2 Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_name)
    # get location of bottom front left corner of tile
    front_left = core_location

    # move cutter to bottom front left corner then up by 0.63 inches
    left_cutter_bottom.location = [
        front_left[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of left cutter bottom
    left_cutter_top = left_cutter_bottom.copy()
    left_cutter_top.name = 'Leg 2 Top.' + tile_name

    add_object_to_collection(left_cutter_top, tile_name)

    # move cutter up by 0.75 inches
    left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters

    right_cutter_bottom = data_to.objects[0].copy()
    right_cutter_bottom.name = 'Leg 1 Bottom.' + tile_name

    add_object_to_collection(right_cutter_bottom, tile_name)
    # get location of bottom front right corner of tile
    front_right = [
        core_location[0] + (tile_props.leg_1_len),
        core_location[1],
        core_location[2]]
    # move cutter to bottom front right corner then up by 0.63 inches
    right_cutter_bottom.location = [
        front_right[0],
        front_right[1] + (base_size[1] / 2),
        front_right[2] + 0.63]
    # rotate cutter 180 degrees around Z
    right_cutter_bottom.rotation_euler[2] = radians(180)

    array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    right_cutter_top = right_cutter_bottom.copy()
    right_cutter_top.name = 'Leg 1 Top.' + tile_name

    add_object_to_collection(right_cutter_top, tile_name)
    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

    array_mod = right_cutter_top.modifiers["Array"]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    left_cutters = [cutters[0], cutters[1]]
    right_cutters = [cutters[2], cutters[3]]

    deselect_all()
    cursor = bpy.context.scene.cursor

    for cutter in right_cutters:
        select(cutter.name)
    bpy.ops.transform.rotate(
        value=radians(tile_props.angle - 90),
        orient_type='GLOBAL',
        orient_axis='Z',
        center_override=cursor.location)

    deselect_all()

    for cutter in left_cutters:
        cutter.location = (
            cutter.location[0] + (tile_props.base_size[1] / 2),
            cutter.location[1] + tile_props.leg_2_len - (tile_props.base_size[1] / 2),
            cutter.location[2])
        cutter.rotation_euler = (0, 0, radians(-90))

    return cutters


def spawn_wall_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    base_thickness = tile_props.base_size[1]
    wall_thickness = tile_props.tile_size[1]
    base_height = tile_props.base_size[2]
    wall_height = tile_props.tile_size[2]
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle
    native_subdivisions = (
        tile_props.leg_1_native_subdivisions,
        tile_props.leg_2_native_subdivisions,
        tile_props.width_native_subdivisions,
        tile_props.z_native_subdivisions)
    thickness_diff = base_thickness - wall_thickness

    # first work out where we're going to start drawing our wall
    # from, taking into account the difference in thickness
    # between the base and wall and how long our legs will be
    core_triangles_1 = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness_diff / 2,
        angle)

    core_x_leg = core_triangles_1['b_adj']
    core_y_leg = core_triangles_1['d_adj']

    # work out dimensions of core
    core_triangles_2 = calculate_corner_wall_triangles(
        core_x_leg,
        core_y_leg,
        wall_thickness,
        angle)

    core = draw_corner_wall_core(
        core_triangles_1,
        core_triangles_2,
        angle,
        wall_thickness,
        thickness_diff,
        base_height,
        wall_height - base_height,
        native_subdivisions
    )

    core.name = tile_props.tile_name + '.core'
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core],
        'selected_editable_objects': [core]
    }

    bpy.context.scene.cursor.location = (0, 0, 0)

    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    core.name = tile_props.tile_name + '.core'
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle
    thickness = tile_props.base_size[1]
    height = tile_props.base_size[2]

    triangles = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle)

    dimensions = {
        'thickness': thickness,
        'height': height,
        'angle': angle,
        'leg_2_len': leg_2_len}
    base = draw_corner_3D_bm(triangles, dimensions)

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle
    thickness = tile_props.base_size[1]

    base = spawn_plain_base(tile_props)

    base_triangles = calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle)

    slot_cutter = create_openlock_base_slot_cutter(tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props)
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    # clip cutters - leg 1
    leg_len = base_triangles['a_adj']
    corner_loc = base.location
    clip_cutter_1 = create_openlock_base_clip_cutter(leg_len, corner_loc, 0.25, tile_props)
    clip_cutter_1.name = 'Clip Leg 1.' + base.name

    ctx = {
        'object': clip_cutter_1,
        'active_object': clip_cutter_1,
        'selected_editable_objects': [clip_cutter_1],
        'selected_objects': [clip_cutter_1]
    }

    bpy.ops.transform.rotate(
        ctx,
        value=radians(tile_props.angle - 90),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=corner_loc)

    # clip cutters - leg 2
    leg_len = base_triangles['c_adj']
    corner_loc = base.location
    clip_cutter_2 = create_openlock_base_clip_cutter(
        leg_len,
        corner_loc,
        0.25,
        tile_props)
    clip_cutter_2.name = 'Clip Leg 2.' + base.name

    ctx = {
        'object': clip_cutter_2,
        'active_object': clip_cutter_2,
        'selected_editable_objects': [clip_cutter_2],
        'selected_objects': [clip_cutter_2]
    }

    bpy.ops.transform.rotate(
        ctx,
        value=radians(-90),
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=corner_loc)

    bpy.ops.transform.mirror(
        ctx,
        orient_type='LOCAL',
        constraint_axis=(False, True, False))

    clip_cutter_2.location[0] = clip_cutter_2.location[0] + 0.5

    cutters = [clip_cutter_1, clip_cutter_2]
    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props)
        set_bool_props(cutter, base, 'DIFFERENCE')

    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.view_layer.objects.active = base

    return base


def create_openlock_base_clip_cutter(
        leg_len,
        corner_loc,
        offset,
        tile_props):
    """Create clip cutters for OpenLOCK base

    Args:
        leg_len (float): outer length
        corner_loc (Vector[3]): cloaction of corner
        offset (float): offset from corner to start clip
        tile_props (bpy.types.MT_Tile_Properties): tile properties

    Returns:
        bpy.type.Object: Clip cutter
    """

    mode('OBJECT')
    # load cutter
    # Get cutter
    deselect_all()
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load base cutters
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = [
            'openlock.wall.base.cutter.clip',
            'openlock.wall.base.cutter.clip.cap.start',
            'openlock.wall.base.cutter.clip.cap.end']

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


def create_openlock_base_slot_cutter(tile_props):
    """Creates the base slot cutter for OpenLOCK tiles

    Args:
        tile_props (bpy.types.MT_Tile_Props): tile properties

    Returns:
        bpy.types.Object: tile cutter
    """
    leg_1_len = tile_props.leg_1_len
    leg_2_len = tile_props.leg_2_len
    angle = tile_props.angle

    face_dist = 0.233
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

    cutter = draw_corner_3D(
        cutter_triangles_2,
        angle,
        slot_width,
        slot_height)

    cutter.name = 'Slot.' + tile_props.tile_name + '.base.cutter'

    return cutter
