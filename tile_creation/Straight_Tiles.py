import os
from math import radians, floor
from mathutils import Vector
import bpy

from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty)

from ..properties.properties import (
    create_base_blueprint_enums,
    create_main_part_blueprint_enums)

from ..properties.scene_props import (
    update_main_part_defaults_2,
    update_base_defaults_2)

from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)

from ..operators.assign_reference_object import (
    create_helper_object)

from ..lib.utils.selection import select, deselect_all, activate
from ..lib.bmturtle.scripts import (
    draw_cuboid,
    draw_straight_wall_core)
from .. lib.utils.utils import mode, get_all_subclasses

from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    convert_to_displacement_core_2,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props,
    copy_annotation_props,
    get_subdivs)

from .Rectangular_Tiles import (
    create_plain_rect_floor_cores,
    spawn_plain_base,
    spawn_openlock_base)


class MT_PT_Straight_Wall_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Straight_Wall_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "STRAIGHT_WALL"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        wall_props = scene.mt_wall_scene_props

        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_z')

        layout.label(text="Core Size")
        layout.prop(scene_props, 'tile_y', text="Width")

        if scene_props.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.label(text="Floor Thickness")
            layout.prop(wall_props, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(wall_props, 'wall_position', text="")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'x_proportionate_scale')
        row.prop(scene_props, 'y_proportionate_scale')
        row.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.operator('scene.reset_wall_defaults')


class MT_PT_Straight_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Straight_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "STRAIGHT_FLOOR"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Size")
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

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.operator('scene.reset_tile_defaults')


def tile_x_update(self, context):
    tile_props = context.collection.mt_tile_props
    if self.x_proportionate_scale and not self.invoked:
        self.base_x = tile_props.base_size[0] + self.tile_x - tile_props.tile_size[0]


def tile_y_update(self, context):
    tile_props = context.collection.mt_tile_props
    if self.y_proportionate_scale and not self.invoked:
        self.base_y = tile_props.base_size[1] + self.tile_y - tile_props.tile_size[1]


def tile_z_update(self, context):
    tile_props = context.collection.mt_tile_props
    if self.z_proportionate_scale and not self.invoked:
        self.base_z = tile_props.base_size[2] + self.tile_z - tile_props.tile_size[2]


class MT_OT_Make_Straight_Wall_Tile(Operator, MT_Tile_Generator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'UNDO', 'REGISTER', "PRESET"}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_WALL"

    # Tile type #
    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        update=update_main_part_defaults_2,
        name="Core"
    )

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_defaults_2,
        name="Base"
    )

    # Dimensions #
    tile_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=2,
        update=tile_x_update,
        min=0
    )

    tile_y: FloatProperty(
        name="Y",
        default=0.3,
        step=50,
        precision=2,
        update=tile_y_update,
        min=0
    )

    tile_z: FloatProperty(
        name="Z",
        default=2.0,
        step=50,
        precision=2,
        update=tile_z_update,
        min=0
    )

    # Base size
    base_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=2,
        min=0
    )

    base_y: FloatProperty(
        name="Y",
        default=0.5,
        step=50,
        precision=2,
        min=0
    )

    base_z: FloatProperty(
        name="Z",
        default=0.3,
        step=50,
        precision=2,
        min=0
    )

    x_proportionate_scale: BoolProperty(
        name="X",
        default=True
    )

    y_proportionate_scale: BoolProperty(
        name="Y",
        default=False
    )

    z_proportionate_scale: BoolProperty(
        name="Z",
        default=False
    )

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)

        if not self.refresh:
            return {'PASS_THROUGH'}

        scene = context.scene
        scene_props = scene.mt_scene_props
        wall_scene_props = scene.mt_wall_scene_props
        base_blueprint = self.base_blueprint
        core_blueprint = self.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_WALL_CORE'
        self.tile_type = 'STRAIGHT_WALL'

        cursor_orig_loc, cursor_orig_rot = initialise_wall_creator_2(self, context)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            wall_core = None
        else:
            wall_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        # We temporarily override tile_props.base_size to generate floor core for S-Tiles.
        # It is easier to do it this way as the PropertyGroup.copy() method produces a dict
        tile_props = context.collection.mt_tile_props

        orig_tile_size = []
        for c, v in enumerate(tile_props.tile_size):
            orig_tile_size.append(v)

        tile_props.tile_size = (
            tile_props.base_size[0],
            tile_props.base_size[1],
            scene_props.base_z + wall_scene_props.floor_thickness)

        if base_blueprint in {'OPENLOCK_S_WALL', 'PLAIN_S_WALL'}:
            floor_core = spawn_prefab(context, subclasses, 'OPENLOCK', 'STRAIGHT_FLOOR_CORE')
            finalise_tile(base, (wall_core, floor_core), cursor_orig_loc, cursor_orig_rot)
        else:
            finalise_tile(base, wall_core, cursor_orig_loc, cursor_orig_rot)

        tile_props.tile_size = orig_tile_size

        if self.auto_refresh is False:
            self.refresh = False

        self.invoked = False

        return {'FINISHED'}

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        layout.prop(self, 'tile_material_1')
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')
        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(self, 'tile_x')
        row.prop(self, 'tile_z')

        layout.label(text="Core Size")
        layout.prop(self, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(self, 'x_proportionate_scale')
        row.prop(self, 'y_proportionate_scale')
        row.prop(self, 'z_proportionate_scale')

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(self, 'base_x')
        row.prop(self, 'base_y')
        row.prop(self, 'base_z')


class MT_OT_Make_Straight_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_floor"
    bl_label = "Straight Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        # scene.render.engine = original_renderer

        return {'FINISHED'}


class MT_OT_Make_Openlock_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK straight base."""

    bl_idname = "object.make_openlock_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_S_Wall_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK S Wall straight base."""

    bl_idname = "object.make_openlock_s_wall_straight_base"
    bl_label = "S Wall Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK_S_WALL"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_S_Wall_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an plain S wall straight base."""

    bl_idname = "object.make_plain_s_wall_straight_base"
    bl_label = "S Wall Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN_S_WALL"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight base."""

    bl_idname = "object.make_plain_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight base."""

    bl_idname = "object.make_empty_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight wall core."""

    bl_idname = "object.make_plain_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        wall_props = context.collection.mt_wall_tile_props
        spawn_plain_wall_cores(self, tile_props, wall_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock straight wall core."""

    bl_idname = "object.make_openlock_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        wall_props = context.collection.mt_wall_tile_props
        base = context.active_object
        spawn_openlock_wall_cores(self, tile_props, wall_props, base)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight wall core."""

    bl_idname = "object.make_empty_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Plain_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight floor core."""

    bl_idname = "object.make_plain_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        create_plain_rect_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock straight floor core."""

    bl_idname = "object.make_openlock_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = context.collection.mt_tile_props
        create_plain_rect_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty straight wall core."""

    bl_idname = "object.make_empty_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "STRAIGHT_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def initialise_wall_creator_2(self, context):
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator_2(self, context)

    create_collection('Walls', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Walls'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    wall_tile_props = tile_collection.mt_wall_tile_props

    self_annotations = self.get_annotations()
    copy_annotation_props(self, tile_props, self_annotations)
    copy_annotation_props(self, wall_tile_props)

    tile_props.tile_name = tile_collection.name
    tile_props.is_mt_collection = True
    tile_props.collection_type = "TILE"

    wall_tile_props.is_wall = True
    tile_props.tile_size = (self.tile_x, self.tile_y, self.tile_z)
    tile_props.base_size = (self.base_x, self.base_y, self.base_z)

    return cursor_orig_loc, cursor_orig_rot


def initialise_tile_creator_2(self, context):
    deselect_all()
    scene = context.scene

    # Root collection to which we add all tiles
    tiles_collection = create_collection('Tiles', scene.collection)

    # create helper object for material mapping
    create_helper_object(context)

    # set tile name
    tile_name = self.tile_type.lower()

    # We create tile at origin and then move it to original location
    # this stops us from having to update the view layer every time
    # we parent an object
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor_orig_rot = cursor.rotation_euler.copy()
    cursor.location = (0, 0, 0)
    cursor.rotation_euler = (0, 0, 0)

    return tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot

def initialise_wall_creator(context):
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
    wall_tile_props = tile_collection.mt_wall_tile_props

    scene_props = context.scene.mt_scene_props
    wall_scene_props = context.scene.mt_wall_scene_props
    create_common_tile_props(scene_props, tile_props, tile_collection)
    copy_annotation_props(wall_scene_props, wall_tile_props)

    wall_tile_props.is_wall = True

    tile_props.tile_type = 'STRAIGHT_WALL'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

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

    tile_props.tile_type = 'STRAIGHT_FLOOR'
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    return cursor_orig_loc, cursor_orig_rot


def spawn_plain_wall_cores(self, tile_props, wall_props):
    """Spawn plain Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    preview_core = spawn_wall_core(self, tile_props, wall_props)
    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core_2(
        preview_core,
        tile_props,
        textured_vertex_groups)
    return preview_core


def spawn_openlock_wall_cores(self, tile_props, wall_props, base):
    """Spawn OpenLOCK core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        base (bpy.types.Object): tile base

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_wall_core(self, tile_props, wall_props)

    wall_cutters = spawn_openlock_wall_cutters(
        core,
        tile_props,
        wall_props)

    if tile_props.tile_size[0] > 1:
        top_pegs = spawn_openlock_top_pegs(
            core,
            tile_props,
            wall_props)

        set_bool_obj_props(top_pegs, base, tile_props, 'UNION')
        set_bool_props(top_pegs, core, 'UNION')

    for wall_cutter in wall_cutters:
        set_bool_obj_props(wall_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(wall_cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core_2(
        core,
        tile_props,
        textured_vertex_groups)

    return core


def spawn_wall_core(self, tile_props, wall_props):
    """Return the core (vertical) part of a straight wall tile."""
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    core_size = [
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]]
    tile_name = tile_props.tile_name
    native_subdivisions = get_subdivs(tile_props.subdivision_density, core_size)

    core = draw_straight_wall_core(
        core_size,
        native_subdivisions)

    core.name = tile_name + '.wall_core'
    add_object_to_collection(core, tile_name)

    if wall_props.wall_position == 'CENTER':
        # move core so centred, move up so on top of base and set origin to world origin
        core.location = (
            core.location[0],
            core.location[1] + (base_size[1] - tile_size[1]) / 2,
            cursor_start_loc[2] + base_size[2])
    elif wall_props.wall_position == 'SIDE':
        core.location = (
            core.location[0],
            core.location[1] + base_size[1] - tile_size[1] - 0.09,
            cursor_start_loc[2] + base_size[2])

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

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_openlock_top_pegs(core, tile_props, wall_props):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        core (bpy.types.Object): tile core
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size

    peg = load_openlock_top_peg(tile_props)

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 0.505
    array_mod.fit_type = 'FIXED_COUNT'
    array_mod.count = 2

    core_location = core.location.copy()

    if wall_props.wall_position == 'CENTER':
        if tile_size[0] < 4 and tile_size[0] >= 1:
            peg.location = (
                core_location[0] + (tile_size[0] / 2) - 0.252,
                core_location[1] + (base_size[1] / 2) + 0.08,
                core_location[2] + tile_size[2])
        else:
            peg.location = (
                core_location[0] + 0.756,
                core_location[1] + (base_size[1] / 2) + 0.08,
                core_location[2] + tile_size[2])

    elif wall_props.wall_position == 'SIDE':
        if tile_size[0] < 4 and tile_size[0] >= 1:
            peg.location = (
                core_location[0] + (tile_size[0] / 2) - 0.252,
                core_location[1] + base_size[1] - 0.33,
                core_location[2] + tile_size[2])
        else:
            peg.location = (
                core_location[0] + 0.756,
                core_location[1] + base_size[1] - 0.33,
                core_location[2] + tile_size[2])

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 2.017
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[0] - 1.3
    return peg


def spawn_openlock_wall_cutters(core, tile_props, wall_props):
    """Creates the cutters for the wall and positions them correctly
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
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_name)
    # get location of bottom front left corner of tile
    front_left = core_location

    # move cutter to bottom front left corner then up by 0.63 inches
    if wall_props.wall_position == 'CENTER':
        left_cutter_bottom.location = [
            front_left[0],
            front_left[1] + (base_size[1] / 2),
            front_left[2] + 0.63]
    elif wall_props.wall_position == 'SIDE':
        left_cutter_bottom.location = [
            front_left[0],
            front_left[1] + base_size[1] - (tile_size[1] / 2) - 0.09,
            front_left[2] + 0.63]

    array_mod = left_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace = [0, 0, 2]
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    # make a copy of left cutter bottom
    left_cutter_top = left_cutter_bottom.copy()
    left_cutter_top.name = 'X Neg Top.' + tile_name

    add_object_to_collection(left_cutter_top, tile_name)

    # move cutter up by 0.75 inches
    left_cutter_top.location[2] = left_cutter_top.location[2] + 0.75

    array_mod = left_cutter_top.modifiers[array_mod.name]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([left_cutter_bottom, left_cutter_top])

    # right side cutters

    right_cutter_bottom = data_to.objects[0].copy()
    right_cutter_bottom.name = 'X Pos Bottom.' + tile_name

    add_object_to_collection(right_cutter_bottom, tile_name)
    # get location of bottom front right corner of tile
    front_right = [
        core_location[0] + (tile_size[0]),
        core_location[1],
        core_location[2]]

    if wall_props.wall_position == 'CENTER':
        # move cutter to bottom front right corner then up by 0.63 inches
        right_cutter_bottom.location = [
            front_right[0],
            front_right[1] + (base_size[1] / 2),
            front_right[2] + 0.63]
    elif wall_props.wall_position == 'SIDE':
        right_cutter_bottom.location = [
            front_right[0],
            front_left[1] + base_size[1] - (tile_size[1] / 2) - 0.09,
            front_right[2] + 0.63]
    # rotate cutter 180 degrees around Z
    right_cutter_bottom.rotation_euler[2] = radians(180)

    array_mod = right_cutter_bottom.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace = [0, 0, 2]
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[2] - 1

    right_cutter_top = right_cutter_bottom.copy()
    right_cutter_top.name = 'X Pos Top.' + tile_name

    add_object_to_collection(right_cutter_top, tile_name)
    right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

    array_mod = right_cutter_top.modifiers["Array"]
    array_mod.fit_length = tile_size[2] - 1.8

    cutters.extend([right_cutter_bottom, right_cutter_top])

    return cutters
