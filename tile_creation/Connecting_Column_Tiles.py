import os
from math import radians
import bpy
from bpy.types import Operator, Panel
from .. utils.registration import get_prefs
from .. lib.utils.utils import get_all_subclasses
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)
from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg)
from ..lib.bmturtle.scripts import (
    draw_cuboid)
from .Rectangular_Tiles import (
    spawn_openlock_base,
    spawn_floor_core)
from ..lib.bmturtle.commands import (
    create_turtle,
    finalise_turtle,
    add_vert,
    fd,
    ri,
    up,
    pu,
    pd,
    home)
from ..lib.bmturtle.helpers import (
    bm_select_all,
    assign_verts_to_group,
    select_verts_in_bounds)


class MT_PT_Connecting_Column_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Connecting_Column_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "CONNECTING_COLUMN"
        return False

    def draw(self, context):
        """Draw the Panel.

        Args:
            context (bpy.context): context
        """
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'column_type')
        layout.prop(scene_props, 'column_socket_style')
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Column Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_y')
        row.prop(scene_props, 'tile_z')

        layout.label(text="Lock Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')
        row.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.label(text="Native Subdivisions")
        row = layout.row()
        row.prop(scene_props, 'x_native_subdivisions')
        row.prop(scene_props, 'y_native_subdivisions')
        row.prop(scene_props, 'z_native_subdivisions')

        layout.prop(scene_props, 'displacement_thickness')
        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Openlock_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK connecting column base."""

    bl_idname = "object.make_openlock_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain connecting column base."""

    bl_idname = "object.make_plain_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Connecting_Column_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty connecting column base."""

    bl_idname = "object.make_empty_connecting_column_base"
    bl_label = "Connecting Column Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CONNECTING_COLUMN_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain connecting column core."""

    bl_idname = "object.make_plain_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_connecting_column_core(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock connecting column core."""

    bl_idname = "object.make_openlock_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_openlock_connecting_column_core(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Connecting_Column_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty connecting column core."""

    bl_idname = "object.make_empty_connecting_column_core"
    bl_label = "Connecting Column Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CONNECTING_COLUMN_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Connecting_Column_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a connecting column tile with a customisable base and main part."""

    bl_idname = "object.make_connecting_column"
    bl_label = "Connecting Column"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "CONNECTING_COLUMN"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'CONNECTING_COLUMN_BASE'
        core_type = 'CONNECTING_COLUMN_CORE'

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_column_creator(
            context,
            scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer

        return {'FINISHED'}


def initialise_column_creator(context, scene_props):
    """Initialise the column creator and set common properties.

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
    create_collection('Columns', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Columns'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.column_type = scene_props.column_type
    tile_props.tile_type = 'CONNECTING_COLUMN'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    tile_props.displacement_thickness = scene_props.displacement_thickness
    tile_props.column_socket_style = scene_props.column_socket_style

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    # make base
    # base = draw_cuboid(base_size)
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_plain_connecting_column_core(tile_props):
    """Return the column core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    column_type = tile_props.column_type
    socket_style = tile_props.column_socket_style
    if socket_style == 'TEXTURED':
        core = spawn_generic_core(tile_props)
        textured_vertex_groups = ['Front', 'Back', 'Left', 'Right']
    else:
        if column_type == 'I':
        core = spawn_I_core(tile_props)
            textured_vertex_groups = ['Front', 'Back']
        elif column_type == 'L':
        core = spawn_L_core(tile_props)
            textured_vertex_groups = ['Front', 'Left']
        elif column_type == 'O':
        core = spawn_O_core(tile_props)
            textured_vertex_groups = ['Front', 'Back', 'Left']
        elif column_type == 'T':
        core = spawn_T_core(tile_props)
            textured_vertex_groups = ['Front']
        elif column_type == 'X':
        core = spawn_X_core(tile_props)
            textured_vertex_groups = []

    convert_to_displacement_core(
        core,
        textured_vertex_groups)

    return core


def spawn_openlock_connecting_column_core(base, tile_props):
    """Return the column core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    cutters = []
    buffers = []
    column_type = tile_props.column_type
    socket_style = tile_props.column_socket_style
    if column_type == 'I':
        if socket_style == 'TEXTURED':
            core = spawn_generic_core(tile_props)
        else:
            core = spawn_I_core(tile_props)
            textured_vertex_groups = ['Front', 'Back']
        cutters = spawn_openlock_I_cutters(
            core,
            tile_props)
    elif column_type == 'L':
        if socket_style == 'TEXTURED':
            core = spawn_generic_core(tile_props)
        else:
            core = spawn_L_core(tile_props)
            textured_vertex_groups = ['Front', 'Left']
        cutters = spawn_openlock_L_cutters(
            core,
            tile_props)
    elif column_type == 'O':
        if socket_style == 'TEXTURED':
            core = spawn_generic_core(tile_props)
        else:
            core = spawn_O_core(tile_props)
            textured_vertex_groups = ['Front', 'Back', 'Left']
        cutters = spawn_openlock_O_cutters(
            core,
            tile_props)
    elif column_type == 'T':
        if socket_style == 'TEXTURED':
            core = spawn_generic_core(tile_props)
        else:
            core = spawn_T_core(tile_props)
            textured_vertex_groups = ['Front']
        cutters = spawn_openlock_T_cutters(
            core,
            tile_props)
    elif column_type == 'X':
        if socket_style == 'TEXTURED':
            core = spawn_generic_core(tile_props)
        else:
            core = spawn_X_core(tile_props)
            textured_vertex_groups = []
        cutters = spawn_openlock_X_cutters(
            core,
            tile_props)

    if socket_style == 'TEXTURED':
        textured_vertex_groups = ['Front', 'Back', 'Left', 'Right']
        buffers = spawn_socket_buffers(cutters)

    for buffer in buffers:
        set_bool_obj_props(buffer, base, tile_props)
        set_bool_props(buffer, core, 'UNION')
    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props)
        set_bool_props(cutter, core, 'DIFFERENCE')

    convert_to_displacement_core(
        core,
        textured_vertex_groups)

    return core


def spawn_openlock_L_cutters(core, tile_props):
    prefs = get_prefs()
    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter and add to collection
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    bottom_right_cutter = data_to.objects[0].copy()
    bottom_right_cutter.name = 'Right Bottom.' + tile_name

    add_object_to_collection(bottom_right_cutter, tile_name)

    # move cutter to position
    front_left = core.location.copy()

    bottom_right_cutter.rotation_euler[2] = radians(180)

    bottom_right_cutter.location = [
        front_left[0] + base_size[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    # add array mod
    array_mod = bottom_right_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of bottom cutter
    top_right_cutter = bottom_right_cutter.copy()
    top_right_cutter.name = 'right Top.' + tile_name

    add_object_to_collection(top_right_cutter, tile_name)

    # move cutter up by 0.75 inches
    top_right_cutter.location[2] = top_right_cutter.location[2] + 0.75

    # adjust array modifier
    array_mod = top_right_cutter.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    # Back bottom
    back_bottom_cutter = bottom_right_cutter.copy()
    back_bottom_cutter.rotation_euler[2] = radians(-90)
    back_bottom_cutter.location[0] = front_left[0] + (base_size[0] / 2)
    back_bottom_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_bottom_cutter.location[2] = back_bottom_cutter.location[2] - 0.001

    # Rename and add to collection
    back_bottom_cutter.name = 'Back Bottom.' + tile_name
    add_object_to_collection(back_bottom_cutter, tile_name)

    # Back top
    back_top_cutter = top_right_cutter.copy()
    back_top_cutter.rotation_euler[2] = radians(-90)
    back_top_cutter.location[0] = front_left[0] + (base_size[0] / 2)
    back_top_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_top_cutter.location[2] = back_top_cutter.location[2] - 0.001

    # Rename and add to collection
    back_top_cutter.name = 'Back Top.' + tile_name
    add_object_to_collection(back_top_cutter, tile_name)

    cutters = [
        bottom_right_cutter,
        top_right_cutter,
        back_top_cutter,
        back_bottom_cutter]

    return cutters


def spawn_openlock_T_cutters(core, tile_props):
    prefs = get_prefs()
    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter and add to collection
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    bottom_left_cutter = data_to.objects[0].copy()
    bottom_left_cutter.name = 'Left Bottom.' + tile_name

    add_object_to_collection(bottom_left_cutter, tile_name)

    # move cutter to position
    front_left = core.location.copy()
    # bottom_left_cutter.rotation_euler[2] = radians(180)
    bottom_left_cutter.location = [
        front_left[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    # add array mod
    array_mod = bottom_left_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of bottom cutter
    top_left_cutter = bottom_left_cutter.copy()
    top_left_cutter.name = 'Left Top.' + tile_name

    add_object_to_collection(top_left_cutter, tile_name)

    # move cutter up by 0.75 inches
    top_left_cutter.location[2] = top_left_cutter.location[2] + 0.75

    # adjust array modifier
    array_mod = top_left_cutter.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    # bottom right
    bottom_right_cutter = bottom_left_cutter.copy()
    bottom_right_cutter.rotation_euler[2] = radians(180)
    bottom_right_cutter.location[0] = bottom_left_cutter.location[0] + (base_size[0])

    # offset to prevent boolean error
    bottom_right_cutter.location[1] = bottom_right_cutter.location[1] + 0.001
    bottom_right_cutter.location[2] = bottom_right_cutter.location[2] + 0.001

    # Rename and add to collection
    bottom_right_cutter.name = 'Right Bottom.'  + tile_name
    add_object_to_collection(bottom_right_cutter, tile_name)

    # top right
    top_right_cutter = top_left_cutter.copy()
    top_right_cutter.rotation_euler[2] = radians(180)
    top_right_cutter.location[0] = top_left_cutter.location[0] + (base_size[0])
    top_right_cutter.location[1] = top_right_cutter.location[1] + 0.001
    top_right_cutter.location[2] = top_right_cutter.location[2] + 0.001

    # Rename and add to colleciton
    top_right_cutter.name = 'Right Top.' + tile_name
    add_object_to_collection(top_right_cutter, tile_name)

    # Back bottom
    back_bottom_cutter = bottom_left_cutter.copy()
    back_bottom_cutter.rotation_euler[2] = radians(-90)
    back_bottom_cutter.location[0] = back_bottom_cutter.location[0] + (base_size[0] / 2)
    back_bottom_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_bottom_cutter.location[2] = back_bottom_cutter.location[2] - 0.001

    # Rename and add to collection
    back_bottom_cutter.name = 'Back Bottom.' + tile_name
    add_object_to_collection(back_bottom_cutter, tile_name)

    # Back top
    back_top_cutter = top_left_cutter.copy()
    back_top_cutter.rotation_euler[2] = radians(-90)
    back_top_cutter.location[0] = back_top_cutter.location[0] + (base_size[0] / 2)
    back_top_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_top_cutter.location[2] = back_top_cutter.location[2] - 0.001

    # Rename and add to collection
    back_top_cutter.name = 'Back Top.' + tile_name
    add_object_to_collection(back_top_cutter, tile_name)

    cutters = [
        bottom_left_cutter,
        top_left_cutter,
        bottom_right_cutter,
        top_right_cutter,
        back_bottom_cutter,
        back_top_cutter]

    return cutters


def spawn_openlock_X_cutters(core, tile_props):
    prefs = get_prefs()
    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter and add to collection
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    bottom_left_cutter = data_to.objects[0].copy()
    bottom_left_cutter.name = 'Left Bottom.' + tile_name

    add_object_to_collection(bottom_left_cutter, tile_name)

    # move cutter to position
    front_left = core.location.copy()
    # bottom_left_cutter.rotation_euler[2] = radians(180)
    bottom_left_cutter.location = [
        front_left[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    # add array mod
    array_mod = bottom_left_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of bottom cutter
    top_left_cutter = bottom_left_cutter.copy()
    top_left_cutter.name = 'Left Top.' + tile_name

    add_object_to_collection(top_left_cutter, tile_name)

    # move cutter up by 0.75 inches
    top_left_cutter.location[2] = top_left_cutter.location[2] + 0.75

    # adjust array modifier
    array_mod = top_left_cutter.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    # bottom right
    bottom_right_cutter = bottom_left_cutter.copy()
    bottom_right_cutter.rotation_euler[2] = radians(180)
    bottom_right_cutter.location[0] = bottom_left_cutter.location[0] + (base_size[0])

    # offset to prevent boolean error
    bottom_right_cutter.location[1] = bottom_right_cutter.location[1] + 0.001
    bottom_right_cutter.location[2] = bottom_right_cutter.location[2] + 0.001

    # Rename and add to collection
    bottom_right_cutter.name = 'Right Bottom.' + tile_name
    add_object_to_collection(bottom_right_cutter, tile_name)

    # top right
    top_right_cutter = top_left_cutter.copy()
    top_right_cutter.rotation_euler[2] = radians(180)
    top_right_cutter.location[0] = top_left_cutter.location[0] + (base_size[0])
    top_right_cutter.location[1] = top_right_cutter.location[1] + 0.001
    top_right_cutter.location[2] = top_right_cutter.location[2] + 0.001

    # Rename and add to colleciton
    top_right_cutter.name = 'Right Top.' + tile_name
    add_object_to_collection(top_right_cutter, tile_name)

    # Front bottom
    front_bottom_cutter = bottom_left_cutter.copy()
    front_bottom_cutter.rotation_euler[2] = radians(90)
    front_bottom_cutter.location[0] = front_bottom_cutter.location[0] + (base_size[0] / 2)
    front_bottom_cutter.location[1] = front_left[1]

    # Offset
    front_bottom_cutter.location[0] = front_bottom_cutter.location[0] + 0.001
    front_bottom_cutter.location[2] = front_bottom_cutter.location[2] + 0.001

    # Rename and add to collection
    front_bottom_cutter.name = 'Front Bottom.' + tile_name
    add_object_to_collection(front_bottom_cutter, tile_name)

    # Front top
    front_top_cutter = top_left_cutter.copy()
    front_top_cutter.rotation_euler[2] = radians(90)
    front_top_cutter.location[0] = front_top_cutter.location[0] + (base_size[0] / 2)
    front_top_cutter.location[1] = front_left[1]

    # Offset
    front_top_cutter.location[0] = front_top_cutter.location[0] + 0.001
    front_top_cutter.location[2] = front_top_cutter.location[2] + 0.001

    # Rename and add to collection
    front_top_cutter.name = 'Front Top.' + tile_name
    add_object_to_collection(front_top_cutter, tile_name)

    # Back bottom
    back_bottom_cutter = bottom_left_cutter.copy()
    back_bottom_cutter.rotation_euler[2] = radians(-90)
    back_bottom_cutter.location[0] = back_bottom_cutter.location[0] + (base_size[0] / 2)
    back_bottom_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_bottom_cutter.location[2] = back_bottom_cutter.location[2] - 0.001

    # Rename and add to collection
    back_bottom_cutter.name = 'Back Bottom.' + tile_name
    add_object_to_collection(back_bottom_cutter, tile_name)

    # Back top
    back_top_cutter = top_left_cutter.copy()
    back_top_cutter.rotation_euler[2] = radians(-90)
    back_top_cutter.location[0] = back_top_cutter.location[0] + (base_size[0] / 2)
    back_top_cutter.location[1] = front_left[1] + base_size[1]
    # offset
    back_top_cutter.location[2] = back_top_cutter.location[2] - 0.001

    # Rename and add to collection
    back_top_cutter.name = 'Back Top.' + tile_name
    add_object_to_collection(back_top_cutter, tile_name)

    cutters = [
        bottom_left_cutter,
        top_left_cutter,
        bottom_right_cutter,
        top_right_cutter,
        back_bottom_cutter,
        back_top_cutter,
        front_bottom_cutter,
        front_top_cutter]

    return cutters


def spawn_socket_buffers(cutters):
    prefs = get_prefs()
    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load buffer mesh
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.meshes = ['socket_buffer']

    buffers = []

    for cutter in cutters:
        buffer = cutter.copy()
        buffer.data = data_to.meshes[0].copy()
        buffer.name = 'Buffer ' + cutter.name
        buffers.append(buffer)

    return buffers


def spawn_openlock_I_cutters(core, tile_props):
    prefs = get_prefs()
    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter and add to collection
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    bottom_left_cutter = data_to.objects[0].copy()
    bottom_left_cutter.name = 'Left Bottom.' + tile_name

    add_object_to_collection(bottom_left_cutter, tile_name)

    # move cutter to position
    front_left = core.location.copy()
    # bottom_left_cutter.rotation_euler[2] = radians(180)
    bottom_left_cutter.location = [
        front_left[0],
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    # add array mod
    array_mod = bottom_left_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of bottom cutter
    top_left_cutter = bottom_left_cutter.copy()
    top_left_cutter.name = 'Left Top.' + tile_name

    add_object_to_collection(top_left_cutter, tile_name)

    # move cutter up by 0.75 inches
    top_left_cutter.location[2] = top_left_cutter.location[2] + 0.75

    # adjust array modifier
    array_mod = top_left_cutter.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    # bottom right
    bottom_right_cutter = bottom_left_cutter.copy()
    bottom_right_cutter.rotation_euler[2] = radians(180)
    bottom_right_cutter.location[0] = bottom_left_cutter.location[0] + (base_size[0])
    # offset to prevent boolean error
    bottom_right_cutter.location[1] = bottom_right_cutter.location[1] + 0.001
    bottom_right_cutter.location[2] = bottom_right_cutter.location[2] + 0.001
    bottom_right_cutter.name = 'Right Bottom.'  + tile_name
    add_object_to_collection(bottom_right_cutter, tile_name)

    # top right
    top_right_cutter = top_left_cutter.copy()
    top_right_cutter.rotation_euler[2] = radians(180)
    top_right_cutter.location[0] = top_left_cutter.location[0] + (base_size[0])
    top_right_cutter.location[1] = top_right_cutter.location[1] + 0.001
    top_right_cutter.location[2] = top_right_cutter.location[2] + 0.001
    top_right_cutter.name = 'Right Top.' + tile_name
    add_object_to_collection(top_right_cutter, tile_name)

    cutters = [bottom_left_cutter, top_left_cutter, bottom_right_cutter, top_right_cutter]
    return cutters


def spawn_openlock_O_cutters(core, tile_props):
    prefs = get_prefs()
    tile_name = tile_props.tile_name
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter and add to collection
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    bottom_cutter = data_to.objects[0].copy()
    bottom_cutter.name = 'Bottom.' + tile_name

    add_object_to_collection(bottom_cutter, tile_name)

    # move cutter to position
    front_left = core.location.copy()
    bottom_cutter.rotation_euler[2] = radians(180)
    bottom_cutter.location = [
        front_left[0] + (base_size[0]),
        front_left[1] + (base_size[1] / 2),
        front_left[2] + 0.63]

    # add array mod
    array_mod = bottom_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of bottom cutter
    top_cutter = bottom_cutter.copy()
    top_cutter.name = 'Top.' + tile_name

    add_object_to_collection(top_cutter, tile_name)

    # move cutter up by 0.75 inches
    top_cutter.location[2] = top_cutter.location[2] + 0.75

    # adjust array modifier
    array_mod = top_cutter.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters = [bottom_cutter, top_cutter]

    return cutters


def spawn_generic_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    disp_thickness = tile_props.displacement_thickness
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    dims = [tile_size[0] - disp_thickness * 2,
            tile_size[1] - disp_thickness * 2,
            tile_size[2] - base_size[2]]

    margin = tile_props.texture_margin

    core, bm, top_verts, bottom_verts, deform_groups = draw_column_core(
        dims,
        native_subdivisions,
        margin)

    make_generic_core_vert_groups(core, bm, dims, margin, top_verts, bottom_verts, deform_groups)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0] + ((base_size[0] - tile_size[0]) / 2) + disp_thickness,
        core.location[1] + ((base_size[1] - tile_size[1]) / 2) + disp_thickness,
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_I_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    disp_thickness = tile_props.displacement_thickness
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    dims = [tile_size[0],
            tile_size[1] - disp_thickness * 2,
            tile_size[2] - base_size[2]]

    margin = tile_props.texture_margin

    core, bm, top_verts, bottom_verts, deform_groups = draw_column_core(
        dims,
        native_subdivisions,
        margin)

    make_I_core_vert_groups(core, bm, dims, margin, top_verts, bottom_verts, deform_groups)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0] + ((base_size[0] - tile_size[0]) / 2),
        core.location[1] + ((base_size[1] - tile_size[1]) / 2) + (disp_thickness),
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_L_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    disp_thickness = tile_props.displacement_thickness
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    dims = [tile_size[0] - disp_thickness,
            tile_size[1] - disp_thickness,
            tile_size[2] - base_size[2]]

    margin = tile_props.texture_margin

    core, bm, top_verts, bottom_verts, deform_groups = draw_column_core(
        dims,
        native_subdivisions,
        margin)

    make_L_core_vert_groups(core, bm, dims, margin, top_verts, bottom_verts, deform_groups)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0] + ((base_size[0] - tile_size[0]) / 2) + disp_thickness,
        core.location[1] + ((base_size[1] - tile_size[1]) / 2) + disp_thickness,
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_O_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    disp_thickness = tile_props.displacement_thickness
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    dims = [tile_size[0] - disp_thickness,
            tile_size[1] - (disp_thickness * 2),
            tile_size[2] - base_size[2]]

    margin = tile_props.texture_margin

    core, bm, top_verts, bottom_verts, deform_groups = draw_column_core(
        dims,
        native_subdivisions,
        margin)

    make_O_core_vert_groups(core, bm, dims, margin, top_verts, bottom_verts, deform_groups)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0] + ((base_size[0] - tile_size[0]) / 2) + disp_thickness,
        core.location[1] + ((base_size[1] - tile_size[1]) / 2) + disp_thickness,
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_T_core(tile_props):
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()

    disp_thickness = tile_props.displacement_thickness
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    native_subdivisions = [
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions]

    dims = [tile_size[0],
            tile_size[1] - disp_thickness,
            tile_size[2] - base_size[2]]

    margin = tile_props.texture_margin

    core, bm, top_verts, bottom_verts, deform_groups = draw_column_core(
        dims,
        native_subdivisions,
        margin)

    make_T_core_vert_groups(core, bm, dims, margin, top_verts, bottom_verts, deform_groups)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    # move core so centred, move up so on top of base and set origin to world origin
    core.location = (
        core.location[0] + ((base_size[0] - tile_size[0]) / 2),
        core.location[1] + ((base_size[1] - tile_size[1]) / 2) + disp_thickness,
        cursor_start_loc[2] + base_size[2])

    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_X_core(tile_props):
    # we only ever want texture on the top of our X column so use the rectangular floor core
    core = spawn_floor_core(tile_props)
    textured_vertex_groups = []
    convert_to_displacement_core(
        core,
        textured_vertex_groups)
    return core


def draw_column_core(dims, subdivs, margin=0.001):
    """Draw a column core and return bmesh.

    Args:
        dims (tuple[3]): X, Y, Z Dimensions
        subdivs (tuple[3]): How many times to subdivide along X, Y, Z dims
        margin (float, optional): Margin to leave around textured areas. Defaults to 0.001.

    Returns:
        bpy.types.Object: core
        bmesh: core bmesh
        list[BMVerts]: list of top verts
        BMVerts.layers.deform: deform groups
    """
    vert_groups = ['Left', 'Right', 'Front', 'Back', 'Top', 'Bottom']

    bm, obj = create_turtle('Straight Wall', vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active
    bm.select_mode = {'VERT'}

    bottom_verts = []
    top_verts = []

    # Start drawing column
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

    # assign bottom verts to vertex groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')

    # home turtle
    pu(bm)

    home(obj)

    return obj, bm, top_verts, bottom_verts, deform_groups


def make_generic_core_vert_groups(obj, bm, dims, margin, top_verts, bottom_verts, deform_groups):
    # select front verts
    lbound = (0, 0, 0)
    ubound = (dims[0], 0, dims[2])
    buffer = margin / 2

    front_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select left verts
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select right verts
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select back side
    lbound = (0, dims[1], 0)
    ubound = (dims[0], dims[1], dims[2])
    buffer = margin / 2

    back_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # ensure vert groups only contain the verts we want.
    front_verts = [v for v in front_verts_orig
                   if v not in right_verts_orig
                   and v not in left_verts_orig
                   and v not in bottom_verts
                   and v not in top_verts]
    left_verts = [v for v in left_verts_orig
                  if v not in bottom_verts
                  and v not in top_verts]
    right_verts = [v for v in right_verts_orig
                   if v not in top_verts
                   and v not in bottom_verts]
    back_verts = [v for v in back_verts_orig
                  if v not in left_verts_orig
                  and v not in right_verts_orig
                  and v not in top_verts
                  and v not in bottom_verts]

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def make_L_core_vert_groups(obj, bm, dims, margin, top_verts, bottom_verts, deform_groups):
    # select front verts
    lbound = (0, 0, 0)
    ubound = (dims[0], 0, dims[2])
    buffer = margin / 2

    front_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select left verts
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select right verts
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select back side
    lbound = (0, dims[1], 0)
    ubound = (dims[0], dims[1], dims[2])
    buffer = margin / 2

    back_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # ensure vert groups only contain the verts we want.
    front_verts = [v for v in front_verts_orig
                   if v not in right_verts_orig
                   and v not in bottom_verts]
    left_verts = [v for v in left_verts_orig
                  if v not in back_verts_orig
                  and v not in bottom_verts]
    right_verts = [v for v in right_verts_orig
                   if v not in front_verts_orig
                   and v not in back_verts_orig
                   and v not in bottom_verts]
    back_verts = [v for v in back_verts_orig
                  if v not in left_verts_orig
                  and v not in right_verts_orig
                  and v not in bottom_verts]

    side_verts = front_verts_orig + back_verts_orig + left_verts_orig + right_verts_orig
    top_verts = [v for v in top_verts if v not in side_verts]

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def make_I_core_vert_groups(obj, bm, dims, margin, top_verts, bottom_verts, deform_groups):
    # select front verts
    lbound = (0, 0, 0)
    ubound = (dims[0], 0, dims[2])
    buffer = margin / 2

    front_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select left verts
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select right verts
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select back side
    lbound = (0, dims[1], 0)
    ubound = (dims[0], dims[1], dims[2])
    buffer = margin / 2

    back_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # ensure vert groups only contain the verts we want.
    front_verts = [v for v in front_verts_orig
                   if v not in right_verts_orig
                   and v not in left_verts_orig
                   and v not in top_verts
                   and v not in bottom_verts]
    left_verts = [v for v in left_verts_orig
                  if v not in back_verts_orig
                  and v not in front_verts_orig
                  and v not in top_verts
                  and v not in bottom_verts]
    right_verts = [v for v in right_verts_orig
                   if v not in front_verts_orig
                   and v not in back_verts_orig
                   and v not in top_verts
                   and v not in bottom_verts]
    back_verts = [v for v in back_verts_orig
                  if v not in left_verts_orig
                  and v not in right_verts_orig
                  and v not in top_verts
                  and v not in bottom_verts]

    side_verts = left_verts_orig + right_verts_orig
    top_verts = [v for v in top_verts if v not in side_verts]

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def make_O_core_vert_groups(obj, bm, dims, margin, top_verts, bottom_verts, deform_groups):
    # select front verts
    lbound = (0, 0, 0)
    ubound = (dims[0], 0, dims[2])
    buffer = margin / 2

    front_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select left verts
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select right verts
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select back side
    lbound = (0, dims[1], 0)
    ubound = (dims[0], dims[1], dims[2])
    buffer = margin / 2

    back_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # ensure vert groups only contain the verts we want.
    front_verts = [v for v in front_verts_orig
                   if v not in right_verts_orig
                   and v not in left_verts_orig
                   and v not in top_verts
                   and v not in bottom_verts]
    left_verts = [v for v in left_verts_orig
                  if v not in top_verts
                  and v not in bottom_verts]
    right_verts = [v for v in right_verts_orig
                   if v not in front_verts_orig
                   and v not in back_verts_orig
                   and v not in top_verts
                   and v not in bottom_verts]
    back_verts = [v for v in back_verts_orig
                  if v not in left_verts_orig
                  and v not in right_verts_orig
                  and v not in top_verts
                  and v not in bottom_verts]
    top_verts = [v for v in top_verts
                 if v not in right_verts_orig]

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')
    assign_verts_to_group(back_verts, obj, deform_groups, 'Back')
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(right_verts, obj, deform_groups, 'Right')
    assign_verts_to_group(left_verts, obj, deform_groups, 'Left')
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj


def make_T_core_vert_groups(obj, bm, dims, margin, top_verts, bottom_verts, deform_groups):
    # select front verts
    lbound = (0, 0, 0)
    ubound = (dims[0], 0, dims[2])
    buffer = margin / 2

    front_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select left verts
    lbound = (0, 0, 0)
    ubound = (0, dims[1], dims[2])
    buffer = margin / 2

    left_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select right verts
    lbound = (dims[0], 0, 0)
    ubound = dims
    buffer = margin / 2

    right_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # select back side
    lbound = (0, dims[1], 0)
    ubound = (dims[0], dims[1], dims[2])
    buffer = margin / 2

    back_verts_orig = select_verts_in_bounds(lbound, ubound, buffer, bm)

    # ensure vert groups only contain the verts we want.
    front_verts = [v for v in front_verts_orig
                   if v not in right_verts_orig
                   and v not in left_verts_orig
                   and v not in top_verts
                   and v not in bottom_verts]

    side_verts = back_verts_orig + left_verts_orig + right_verts_orig
    top_verts = [v for v in top_verts if v not in side_verts]

    assign_verts_to_group(front_verts, obj, deform_groups, 'Front')
    assign_verts_to_group(back_verts_orig, obj, deform_groups, 'Back')
    assign_verts_to_group(top_verts, obj, deform_groups, 'Top')
    assign_verts_to_group(right_verts_orig, obj, deform_groups, 'Right')
    assign_verts_to_group(left_verts_orig, obj, deform_groups, 'Left')
    # finalise turtle and release bmesh
    finalise_turtle(bm, obj)

    return obj
