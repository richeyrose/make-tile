import os
import math
import bpy

from bpy.types import Operator, Panel
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.utils.utils import mode, get_all_subclasses
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.straight_tile import draw_rectangular_floor_core
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base
from .. lib.utils.selection import deselect_all, select_by_loc
from .create_tile import create_displacement_core, finalise_tile


class MT_PT_Openlock_Rect_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Openlock_Rect_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check mt_tile_type_new."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.mt_tile_type_new == "object.make_openlock_rect_floor"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'mt_tile_x')
        row.prop(scene_props, 'mt_tile_y')
        row.prop(scene_props, 'mt_tile_z')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'mt_base_x')
        row.prop(scene_props, 'mt_base_y')
        row.prop(scene_props, 'mt_base_z')


class MT_PT_Plain_Rect_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Plain_Rect_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check mt_tile_type_new."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.mt_tile_type_new == "object.make_plain_rect_floor"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'mt_tile_x')
        row.prop(scene_props, 'mt_tile_y')
        row.prop(scene_props, 'mt_tile_z')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'mt_base_x')
        row.prop(scene_props, 'mt_base_y')
        row.prop(scene_props, 'mt_base_z')


class MT_PT_Custom_Rect_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Custom_Rect_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check mt_tile_type_new."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.mt_tile_type_new == "object.make_custom_rect_floor"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.prop(scene_props, 'mt_base_blueprint')
        layout.prop(scene_props, 'mt_main_part_blueprint')

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'mt_tile_x')
        row.prop(scene_props, 'mt_tile_y')
        row.prop(scene_props, 'mt_tile_z')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'mt_base_x')
        row.prop(scene_props, 'mt_base_y')
        row.prop(scene_props, 'mt_base_z')


class MT_OT_Make_Openlock_Rect_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK rectangular base."""

    bl_idname = "object.make_openlock_rect_base"
    bl_label = "Rectangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "RECT_FLOOR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Rect_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain rectangular base."""

    bl_idname = "object.make_plain_rect_base"
    bl_label = "Rectangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "RECT_FLOOR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Rect_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain rectangular core."""

    bl_idname = "object.make_plain_rect_floor_core"
    bl_label = "Rectangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "RECT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        create_plain_rect_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Rect_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock rectangular floor core."""

    bl_idname = "object.make_openlock_rect_floor_core"
    bl_label = "Rectangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "RECT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        bpy.ops.object.make_plain_rect_floor_core()
        return{'FINISHED'}


class MT_OT_Make_Custom_Rect_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a rectangular floor tile with a customisable base and main part."""

    bl_idname = "object.make_custom_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "RECT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_type = scene_props.mt_base_blueprint
        core_type = scene_props.mt_main_part_blueprint
        subclasses = get_all_subclasses(MT_Tile_Generator)

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)

        # ensure we can only run bpy.ops in our eval statements
        allowed_names = {k: v for k, v in bpy.__dict__.items() if k == 'ops'}

        for subclass in subclasses:
            if hasattr(subclass, 'mt_type') and hasattr(subclass, 'mt_blueprint'):
                if subclass.mt_type == 'RECT_FLOOR_BASE' and subclass.mt_blueprint == base_type:
                    eval_str = 'ops.' + subclass.bl_idname + '()'
                    eval(eval_str, {"__builtins__": {}}, allowed_names)

        base = context.active_object

        for subclass in subclasses:
            if hasattr(subclass, 'mt_type') and hasattr(subclass, 'mt_blueprint'):
                if subclass.mt_type == 'RECT_FLOOR_CORE' and subclass.mt_blueprint == core_type:
                    eval_str = 'ops.' + subclass.bl_idname + '()'
                    eval(eval_str, {"__builtins__": {}}, allowed_names)

        preview_core = context.active_object

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer
        print("Make Custom rect floor")

        return {'FINISHED'}


class MT_OT_Make_Plain_Rect_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a rectangular floor tile."""

    bl_idname = "object.make_plain_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'REGISTER', 'UNDO'}
    mt_blueprint = "PLAIN"
    mt_type = "RECT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)
        bpy.ops.object.make_plain_rect_base()
        base = context.active_object
        bpy.ops.object.make_plain_rect_floor_core()
        preview_core = context.active_object
        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # reset render engine
        scene.render.engine = original_renderer
        return {'FINISHED'}


class MT_OT_Make_Openlock_Rect_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a rectangular floor tile."""

    bl_idname = "object.make_openlock_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "OPENLOCK"
    mt_type = "RECT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)
        bpy.ops.object.make_openlock_rect_base()
        base = context.active_object
        bpy.ops.object.make_plain_rect_floor_core()
        preview_core = context.active_object
        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # reset render engine
        scene.render.engine = original_renderer
        return {'FINISHED'}


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
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'RECTANGULAR_FLOOR'
    tile_props.tile_size = (scene_props.mt_tile_x, scene_props.mt_tile_y, scene_props.mt_tile_z)
    tile_props.base_size = (scene_props.mt_base_x, scene_props.mt_base_y, scene_props.mt_base_z)

    tile_props.x_native_subdivisions = scene_props.mt_x_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.mt_y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.mt_z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def create_plain_rect_floor_cores(base, tile_props):
    """Create preview and displacement cores.

    Args:
        base (bpy.types.Object): tile base
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_floor_core(tile_props)
    textured_vertex_groups = ['Top']

    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    bpy.context.view_layer.objects.active = preview_core

    return preview_core


def spawn_floor_core(tile_props):
    """Spawn the core (top part) of a floor tile.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile core
    """
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name
    native_subdivisions = (
        tile_props.x_native_subdivisions,
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions
    )

    core = draw_rectangular_floor_core(
        [tile_size[0],
            tile_size[1],
            tile_size[2] - base_size[2]],
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    core.location[2] = cursor_start_loc[2] + base_size[2]

    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

    make_rect_floor_vert_groups(core)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    base_size = tile_props.base_size
    tile_name = tile_props.tile_name

    # make base
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base]}

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn an openlock base into the scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    tile_name = tile_props.tile_name
    base_size = tile_props.base_size

    base = draw_openlock_rect_floor_base(base_size)
    base.name = tile_props.tile_name + '.base'
    mode('OBJECT')

    add_object_to_collection(base, tile_props.tile_name)

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base]
    }

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name

    base.location = (
        base.location[0] + base_size[0] / 2,
        base.location[1] + base_size[1] / 2,
        base.location[2]
    )

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    clip_cutters = spawn_openlock_base_clip_cutters(base, tile_props)

    for clip_cutter in clip_cutters:
        clip_cutter.parent = base
        clip_cutter.display_type = 'BOUNDS'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter

    mode('OBJECT')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_clip_cutters(base, tile_props):
    """Make cutters for the openlock base clips.

    Args:
        base (bpy.types.Object): tile base
        tile_props (mt_tile_props): tile properties

    Returns:
        list of base clip cutters

    """
    mode('OBJECT')

    base_location = base.location.copy()
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

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

    # get location of bottom front left corner of tile
    front_left = (
        base_location[0],
        base_location[1],
        base_location[2])

    clip_cutter.location = (
        front_left[0] + 0.5,
        front_left[1] + 0.25,
        front_left[2])

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base.dimensions[0] - 1

    clip_cutter2 = clip_cutter.copy()
    clip_cutter2.data = clip_cutter2.data.copy()

    add_object_to_collection(clip_cutter2, tile_props.tile_name)
    clip_cutter2.rotation_euler = (0, 0, math.radians(90))

    front_right = (
        base_location[0] + base.dimensions[0],
        base_location[1],
        base_location[2])

    clip_cutter2.location = (
        front_right[0] - 0.25,
        front_right[1] + 0.5,
        front_right[2])

    array_mod2 = clip_cutter2.modifiers['Array']
    array_mod2.fit_type = 'FIT_LENGTH'
    array_mod2.fit_length = base.dimensions[1] - 1

    clip_cutter3 = clip_cutter.copy()
    clip_cutter3.data = clip_cutter3.data.copy()
    add_object_to_collection(clip_cutter3, tile_props.tile_name)

    clip_cutter3.rotation_euler = (0, 0, math.radians(180))

    clip_cutter3.location = (
        clip_cutter.location[0] + base.dimensions[0] - 1,
        clip_cutter.location[1] + base.dimensions[1] - 0.5,
        clip_cutter.location[2]
    )
    array_mod3 = clip_cutter3.modifiers['Array']
    array_mod3.fit_type = 'FIT_LENGTH'
    array_mod3.fit_length = base.dimensions[0] - 1

    clip_cutter4 = clip_cutter2.copy()
    clip_cutter4.data = clip_cutter4.data.copy()
    add_object_to_collection(clip_cutter4, tile_props.tile_name)

    clip_cutter4.rotation_euler = (0, 0, math.radians(-90))

    clip_cutter4.location = (
        clip_cutter2.location[0] - base.dimensions[0] + 0.5,
        clip_cutter2.location[1] + base.dimensions[1] - 1,
        clip_cutter2.location[2]
    )

    array_mod4 = clip_cutter4.modifiers['Array']
    array_mod4.fit_type = 'FIT_LENGTH'
    array_mod4.fit_length = base.dimensions[1] - 1

    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

    return [clip_cutter, clip_cutter2, clip_cutter3, clip_cutter4]


def make_rect_floor_vert_groups(core):
    """Make a vertex group for each side of floor and assigns vertices to it.

    Args:
        core (bpy.types.Object): tile core
    """
    mode('OBJECT')
    dim = core.dimensions / 2

    # get original location of object origin and of cursor
    obj_original_loc = core.location.copy()
    cursor_original_loc = bpy.context.scene.cursor.location.copy()

    # set origin to center of bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # make vertex groups
    core.vertex_groups.new(name='Left')
    core.vertex_groups.new(name='Right')
    core.vertex_groups.new(name='Front')
    core.vertex_groups.new(name='Back')
    core.vertex_groups.new(name='Top')
    core.vertex_groups.new(name='Bottom')

    mode('EDIT')

    # select X- and assign to X-
    select_by_loc(
        lbound=[-dim[0], -dim[1], -dim[2]],
        ubound=[-dim[0] + 0.001, dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)

    bpy.ops.object.vertex_group_set_active(group='Left')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select X+ and assign to X+
    select_by_loc(
        lbound=[dim[0] - 0.001, -dim[1], -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Right')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y- and assign to Y-
    select_by_loc(
        lbound=[-dim[0], -dim[1], -dim[2]],
        ubound=[dim[0], -dim[1] + 0.001, dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Front')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y+ and assign to Y+
    select_by_loc(
        lbound=[-dim[0], dim[1] - 0.001, -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Back')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z- and assign to Z-
    select_by_loc(
        lbound=[-dim[0] + 0.001, -dim[1] + 0.001, -dim[2]],
        ubound=[dim[0] - 0.001, dim[1] - 0.001, -dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z+ and assign to Z+
    select_by_loc(
        lbound=[-dim[0] + 0.001, -dim[1] + 0.001, dim[2]],
        ubound=[dim[0] - 0.001, dim[1] - 0.001, dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    mode('OBJECT')

    # reset cursor and object origin
    bpy.context.scene.cursor.location = obj_original_loc
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = cursor_original_loc
