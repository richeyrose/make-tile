import os
from math import radians, pi, modf, degrees
from mathutils import Vector
import bpy
from bpy import context
from bpy.types import Operator, Panel
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. utils.registration import get_prefs
from ..lib.bmturtle.scripts import (
    draw_straight_wall_core,
    draw_rectangular_floor_core,
    draw_curved_cuboid)
from .. lib.utils.selection import (
    deselect_all,
    select,
    activate)
from .. lib.utils.utils import (
    add_circle_array,
    get_all_subclasses)
from .create_tile import (
    convert_to_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

# TODO #2 Fix bug where base sockets are not displaying correctly on bases more than 0.5 inches wide
class MT_PT_Curved_Wall_Tile_Panel(Panel):
    """Draw a tile options panel in the UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 1
    bl_idname = "MT_PT_Curved_Wall_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type in [
                "CURVED_WALL"]
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
        layout.prop(scene_props, 'degrees_of_arc')
        layout.prop(scene_props, 'base_socket_side', text="Socket Side")
        layout.prop(scene_props, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'y_proportionate_scale', text="Width")
        row.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text="Width")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Native Subdivisions")
        row = layout.row()
        row.prop(scene_props, 'curve_native_subdivisions')
        row.prop(scene_props, 'y_native_subdivisions')
        row.prop(scene_props, 'z_native_subdivisions')

        layout.operator('scene.reset_tile_defaults')


class MT_PT_Curved_Floor_Tile_Panel(Panel):
    """Draw a tile options panel in the UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 1
    bl_idname = "MT_PT_Curved_Floor_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type in [
                "CURVED_FLOOR"]
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
        layout.prop(scene_props, 'degrees_of_arc')
        layout.prop(scene_props, 'base_socket_side', text="Socket Side")
        layout.prop(scene_props, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'y_proportionate_scale', text="Width")
        row.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text="Width")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Native Subdivisions")
        row = layout.row()
        row.prop(scene_props, 'curve_native_subdivisions')
        row.prop(scene_props, 'y_native_subdivisions')
        row.prop(scene_props, 'z_native_subdivisions')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Curved_Wall_Tile(MT_Tile_Generator, Operator):
    """Create a Curved Wall Tile."""

    bl_idname = "object.make_curved_wall"
    bl_label = "Curved Wall"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "CURVED_WALL"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'CURVED_BASE'
        core_type = 'CURVED_WALL_CORE'

        cursor_orig_loc, cursor_orig_rot = initialise_wall_creator(
            context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # scene.render.engine = original_renderer
        return {'FINISHED'}


class MT_OT_Make_Curved_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Curved Floor Tile."""

    bl_idname = "object.make_curved_floor"
    bl_label = "Curved Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "CURVED_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'CURVED_BASE'
        core_type = 'CURVED_FLOOR_CORE'

        cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(
            context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # scene.render.engine = original_renderer
        return {'FINISHED'}


class MT_OT_Make_Openlock_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK curved base."""

    bl_idname = "object.make_openlock_curved_base"
    bl_label = "OpenLOCK Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved base."""

    bl_idname = "object.make_plain_curved_base"
    bl_label = "Plain Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved base."""

    bl_idname = "object.make_empty_curved_base"
    bl_label = "Empty Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved wall core."""

    bl_idname = "object.make_plain_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_wall_cores(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock curved wall core."""

    bl_idname = "object.make_openlock_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_openlock_wall_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved wall core."""

    bl_idname = "object.make_empty_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Plain_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved wall core."""

    bl_idname = "object.make_plain_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock curved wall core."""

    bl_idname = "object.make_openlock_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved wall core."""

    bl_idname = "object.make_empty_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_FLOOR_CORE"

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
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Walls', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Walls'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'CURVED_WALL'

    tile_props.base_radius = scene_props.base_radius
    tile_props.degrees_of_arc = scene_props.degrees_of_arc
    tile_props.base_socket_side = scene_props.base_socket_side

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.curve_native_subdivisions = scene_props.curve_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return cursor_orig_loc, cursor_orig_rot


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
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'CURVED_FLOOR'

    tile_props.base_radius = scene_props.base_radius
    tile_props.degrees_of_arc = scene_props.degrees_of_arc
    tile_props.base_socket_side = scene_props.base_socket_side

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.curve_native_subdivisions = scene_props.curve_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return cursor_orig_loc, cursor_orig_rot


def spawn_plain_wall_cores(tile_props):
    """Spawn plain wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    offset = (tile_props.base_size[1] - tile_props.tile_size[1]) / 2
    tile_props.core_radius = tile_props.base_radius + offset
    textured_vertex_groups = ['Front', 'Back']
    preview_core = spawn_wall_core(tile_props)
    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)

    return preview_core


def spawn_openlock_wall_cores(base, tile_props):
    """Spawn OpenLOCK wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    offset = (tile_props.base_size[1] - tile_props.tile_size[1]) / 2
    tile_props.core_radius = tile_props.base_radius + offset

    core = spawn_wall_core(tile_props)

    cutters = spawn_openlock_wall_cutters(
        core,
        base.location,
        tile_props)

    top_peg = spawn_openlock_top_pegs(
        base,
        tile_props)

    set_bool_obj_props(top_peg, base, tile_props, 'UNION')
    set_bool_props(top_peg, core, 'UNION')

    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        core,
        textured_vertex_groups)

    activate(core.name)

    return core


def spawn_openlock_top_pegs(base, tile_props):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """
    base_size = tile_props.base_size
    tile_size = tile_props.tile_size
    base_radius = tile_props.base_radius
    peg = load_openlock_top_peg(tile_props)

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 0.505
    array_mod.fit_type = 'FIXED_COUNT'
    array_mod.count = 2

    base_location = base.location.copy()

    if base_radius >= 1:
        if tile_props.base_socket_side == 'INNER':
            peg.location = (
                base_location[0] - 0.25,
                base_location[1] + base_radius + (base_size[1] / 2) + 0.075,
                base_location[2] + tile_size[2])
        else:
            peg.location = (
                base_location[0] - 0.25,
                base_location[1] + base_radius + (base_size[1] / 2) - 0.075,
                base_location[2] + tile_size[2])

    ctx = {
        'object': peg,
        'active_object': peg,
        'selected_objects': [peg],
        'selected_editable_objects': [peg]
    }

    bpy.ops.transform.rotate(
        ctx,
        value=radians(tile_props.degrees_of_arc / 2) * -1,
        orient_axis='Z',
        orient_type='GLOBAL',
        orient_matrix_type='GLOBAL',
        orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        center_override=base_location)

    return peg


def spawn_openlock_wall_cutters(core, base_location, tile_props):
    """Spawn OpenLOCK wall cutters into scene and position them.

    Args:
        core (bpy.types.Object): tile core
        base_location (Vector[3]): base location
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        list[bpy.types.Objects]: cutters
    """
    deselect_all()

    tile_name = tile_props.tile_name

    preferences = get_prefs()
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
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_props.tile_name)

    # move cutter to origin up by 0.63 inches - base height
    left_cutter_bottom.location = Vector((
        core_location[0],
        core_location[1] + (tile_props.tile_size[1] / 2),
        core_location[2] + 0.63 - tile_props.base_size[2]))

    # add array mod
    array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_props.tile_size[2] - 1

    # make a copy of left cutter bottom
    left_cutter_top = left_cutter_bottom.copy()
    add_object_to_collection(left_cutter_top, tile_props.tile_name)
    left_cutter_top.name = 'X Neg Top.' + tile_name

    # move cutter up by 0.75 inches
    left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

    # modify array
    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_props.tile_size[2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters
    right_cutter_bottom = left_cutter_bottom.copy()
    right_cutter_bottom.rotation_euler[2] = radians(180)
    add_object_to_collection(right_cutter_bottom, tile_props.tile_name)

    right_cutter_bottom.name = 'X Pos Bottom.' + tile_name
    circle_center = base_location
    select(right_cutter_bottom.name)
    activate(right_cutter_bottom.name)

    bpy.ops.transform.rotate(
        value=radians(tile_props.degrees_of_arc) * -1,
        orient_axis='Z',
        orient_type='GLOBAL',
        center_override=circle_center)

    right_cutter_top = right_cutter_bottom.copy()
    add_object_to_collection(right_cutter_top, tile_props.tile_name)
    right_cutter_top.name = 'X Pos Top.' + tile_name

    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75
    # modify array
    array_mod = right_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_props.tile_size[2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    radius = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    deg = tile_props.degrees_of_arc
    height = tile_props.base_size[2]
    width = tile_props.base_size[1]

    base = draw_curved_cuboid(
        tile_props.tile_name + '.base',
        radius,
        segments,
        deg,
        height,
        width)

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(base, tile_props, offset=0.236):
    """Spawns an openlock base slot cutter into the scene and positions it correctly

    Args:
        base (bpy.types.Object): base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        offset (float, optional): Offset from base end along x. Defaults to 0.236.

    Returns:
        bpy.types.Object: slot cutter
    """
    clip_side = tile_props.base_socket_side
    base_radius = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    base_degrees = tile_props.degrees_of_arc

    cutter_w = 0.181
    cutter_h = 0.24

    if clip_side == 'INNER':
        cutter_radius = base_radius + 0.25
    else:
        cutter_radius = base_radius + tile_props.base_size[1] - 0.18 - 0.25

    bool_overlap = 0.001  # overlap amount to prevent errors

    cutter_inner_arc_len = (2 * pi * cutter_radius) / (360 / base_degrees) - (offset * 2)
    central_angle = degrees(cutter_inner_arc_len / cutter_radius)

    slot_cutter = draw_curved_cuboid(
        'Slot.' + tile_props.tile_name,
        cutter_radius,
        segments,
        central_angle,
        cutter_h + bool_overlap,
        cutter_w
    )

    slot_cutter.location[2] = slot_cutter.location[2] - bool_overlap
    slot_cutter.rotation_euler[2] = slot_cutter.rotation_euler[2] - radians((base_degrees - central_angle) / 2)

    ctx = {
        'object': slot_cutter,
        'active_object': slot_cutter,
        'selected_editable_objects': [slot_cutter],
        'selected_objects': [slot_cutter]
    }

    base.select_set(False)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    return slot_cutter


def spawn_openlock_base(tile_props):
    """Spawn OpenLOCK base into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base
    """
    radius = tile_props.base_radius
    segments = tile_props.curve_native_subdivisions
    deg = tile_props.degrees_of_arc
    height = tile_props.base_size[2]
    width = tile_props.base_size[1]

    base = draw_curved_cuboid(
        tile_props.tile_name + '.base',
        radius,
        segments,
        deg,
        height,
        width)

    slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name

    spawn_openlock_base_clip_cutter(base, tile_props)

    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_clip_cutter(base, tile_props):
    """Spawn base clip cutter into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base clip cutter
    """
    scene = bpy.context.scene
    cursor_orig_loc = scene.cursor.location.copy()
    clip_side = tile_props.base_socket_side

    # load base cutter
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    clip_cutter = data_to.objects[0]
    add_object_to_collection(clip_cutter, tile_props.tile_name)
    deselect_all()
    select(clip_cutter.name)

    if clip_side == 'INNER':
        radius = tile_props.base_radius + 0.25
    else:
        radius = tile_props.base_radius + tile_props.base_size[1] - 0.25

    clip_cutter.location[1] = radius


    if clip_side == 'OUTER':
        clip_cutter.rotation_euler[2] = radians(180)

    num_cutters = modf((tile_props.degrees_of_arc - 22.5) / 22.5)
    circle_center = cursor_orig_loc

    if num_cutters[1] == 1:
        initial_rot = (tile_props.degrees_of_arc / 2)

    else:
        initial_rot = 22.5

    bpy.ops.transform.rotate(
        value=radians(initial_rot) * -1,
        orient_axis='Z',
        center_override=circle_center)

    bpy.ops.object.transform_apply(
        location=False,
        scale=False,
        rotation=True,
        properties=False)

    array_name, empty = add_circle_array(
        clip_cutter,
        tile_props.tile_name,
        circle_center,
        num_cutters[1],
        'Z',
        22.5 * -1)

    empty.parent = base

    #empty.hide_set(True)
    empty.hide_viewport = True
    clip_cutter.name = 'Clip.' + base.name
    set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(clip_cutter, base, 'DIFFERENCE')

    return clip_cutter


def spawn_plain_floor_cores(base, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    textured_vertex_groups = ['Top']
    tile_props.core_radius = tile_props.base_radius
    preview_core = spawn_floor_core(tile_props)

    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups)

    return preview_core


def spawn_floor_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    angle = tile_props.degrees_of_arc
    radius = tile_props.core_radius
    width = tile_props.tile_size[1]
    height = tile_props.tile_size[2] - tile_props.base_size[2]
    inner_circumference = 2 * pi * radius
    floor_length = inner_circumference / (360 / angle)
    tile_name = tile_props.tile_name
    native_subdivisions = (
        tile_props.curve_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions
    )

    # Rather than creating our cores as curved objects we create them as straight cuboids
    # and then add a deform modifier. This allows us to not use the modifier when baking the
    # displacement texture by disabling it in render and thus being able to use
    # standard projections

    core = draw_rectangular_floor_core(
        (floor_length,
         width,
         height),
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_props.tile_name)

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    tile_props.tile_size[0] = floor_length

    core.location = (
        core.location[0],
        core.location[1] + radius,
        core.location[2] + tile_props.base_size[2])

    mod = core.modifiers.new('Simple_Deform', type='SIMPLE_DEFORM')
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Z'
    mod.angle = radians(-angle)

    scene_props = bpy.context.scene.mt_scene_props

    # this controls whether the texture follows the curvature of the tile on render.
    # Useful for decorative elements.
    if scene_props.curve_texture:
        mod.show_render = False

    core.name = tile_props.tile_name + '.core'

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_wall_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    angle = tile_props.degrees_of_arc
    radius = tile_props.core_radius
    width = tile_props.tile_size[1]
    height = tile_props.tile_size[2] - tile_props.base_size[2]
    inner_circumference = 2 * pi * radius
    wall_length = inner_circumference / (360 / angle)
    tile_name = tile_props.tile_name
    native_subdivisions = (
        tile_props.curve_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions
    )

    # Rather than creating our cores as curved objects we create them as straight cuboids
    # and then add a deform modifier. This allows us to not use the modifier when baking the
    # displacement texture by disabling it in render and thus being able to use
    # standard projections

    core = draw_straight_wall_core(
        (wall_length,
         width,
         height),
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_props.tile_name)

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    tile_props.tile_size[0] = wall_length

    core.location = (
        core.location[0],
        core.location[1] + radius,
        core.location[2] + tile_props.base_size[2])

    mod = core.modifiers.new('Simple_Deform', type='SIMPLE_DEFORM')
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Z'
    mod.angle = radians(-angle)
    mod.show_render = False
    core.name = tile_props.tile_name + '.core'

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core
