import os
from math import radians

import bpy
from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    BoolProperty,
    StringProperty,
    FloatVectorProperty)

from ..properties.properties import (
    create_base_blueprint_enums,
    create_main_part_blueprint_enums)


from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection)

from ..lib.bmturtle.scripts import (
    draw_straight_wall_core,
    draw_cuboid,
    draw_rectangular_floor_core)

from .. lib.utils.utils import mode, get_all_subclasses

from .create_tile import (
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    get_subdivs,
    tile_x_update,
    tile_y_update,
    tile_z_update)


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
            layout.prop(scene_props, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(scene_props, 'wall_position', text="")

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

        layout.operator('scene.reset_tile_defaults')


class MT_PT_Rect_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Rect_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "RECT_FLOOR"
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


class MT_Straight_Tile:
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
        default=True
    )

    z_proportionate_scale: BoolProperty(
        name="Z",
        default=False
    )

    tile_size: FloatVectorProperty(
        name="Tile Size"
    )

    base_size: FloatVectorProperty(
        name="Base size"
    )


class MT_OT_Make_Straight_Wall_Tile(Operator, MT_Straight_Tile, MT_Tile_Generator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_WALL"

    def update_base_blueprint_enums(self, context):
        if not self.invoked:
            if self.base_blueprint in ("OPENLOCK", "PLAIN"):
                self.base_y = 0.5
                self.base_z = 0.2755
            elif self.base_blueprint in ("OPENLOCK_S_WALL", "PLAIN_S_WALL"):
                self.base_y = 1.0
                self.base_z = 0.2755
            else:
                self.base_y = self.tile_y
                self.base_z = 0.0

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        name="Wall")

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_blueprint_enums,
        name="Base"
    )

    # S Wall Props
    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base.")],
        default="CENTER")

    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}

        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = self.base_blueprint
        wall_blueprint = self.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_WALL_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        kwargs = {"tile_name": self.tile_name}
        base = spawn_prefab(context, subclasses, base_blueprint, base_type, **kwargs)

        kwargs["base_name"] = base.name
        if wall_blueprint == 'NONE':
            wall_core = None
        else:
            wall_core = spawn_prefab(context, subclasses, wall_blueprint, core_type, **kwargs)

        # We temporarily override tile_props.base_size to generate floor core for S-Tiles.
        # It is easier to do it this way as the PropertyGroup.copy() method produces a dict
        tile_props = context.collection.mt_tile_props

        orig_tile_size = []
        for c, v in enumerate(tile_props.tile_size):
            orig_tile_size.append(v)

        tile_props.tile_size = (
            tile_props.base_size[0],
            tile_props.base_size[1],
            scene_props.base_z + self.floor_thickness)

        if base_blueprint in {'OPENLOCK_S_WALL', 'PLAIN_S_WALL'}:
            floor_core = spawn_prefab(context, subclasses, 'OPENLOCK', 'STRAIGHT_FLOOR_CORE', **kwargs)
            self.finalise_tile(context, base, wall_core, floor_core)
        else:
            self.finalise_tile(context, base, wall_core)

        tile_props.tile_size = orig_tile_size

        return {'FINISHED'}

    def init(self, context):
        super().init(context)
        tile_collection = bpy.data.collections[self.tile_name]
        tile_props = tile_collection.mt_tile_props
        tile_props.collection_type = "TILE"
        tile_props.tile_size = (self.tile_x, self.tile_y, self.tile_z)
        tile_props.base_size = (self.base_x, self.base_y, self.base_z)

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        layout.prop(self, 'tile_material_1')
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')
        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(self, 'tile_x')
        row.prop(self, 'tile_y')
        row.prop(self, 'tile_z')

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
        if self.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.label(text="Floor Thickness")
            layout.prop(self, 'floor_thickness', text="")
            layout.label(text="Wall Position")
            layout.prop(self, 'wall_position', text="")


class MT_OT_Make_Rect_Floor_Tile(Operator, MT_Straight_Tile, MT_Tile_Generator):
    """Operator. Generates a rectangular floor tile with a customisable base and main part."""

    bl_idname = "object.make_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "RECT_FLOOR"

    def update_base_blueprint_enums(self, context):
        if not self.invoked:
            if self.base_blueprint in ("OPENLOCK", "PLAIN"):
                self.base_x = self.tile_x
                self.base_y = self.tile_y
                self.base_z = 0.2755
            else:
                self.base_x = self.tile_x
                self.base_y = self.tile_y
                self.base_z = 0.0

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        name="Core"
    )

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_blueprint_enums,
        name="Base"
    )

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}

        base_blueprint = self.base_blueprint
        core_blueprint = self.main_part_blueprint
        base_type = 'STRAIGHT_BASE'
        core_type = 'STRAIGHT_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        kwargs = {"tile_name": self.tile_name}
        base = spawn_prefab(context, subclasses, base_blueprint, base_type, **kwargs)

        kwargs["base_name"] = base.name
        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type, **kwargs)

        self.finalise_tile(context, base, preview_core)

        return {'FINISHED'}

    def init(self, context):
        super().init(context)
        tile_collection = bpy.data.collections[self.tile_name]
        tile_props = tile_collection.mt_tile_props
        tile_props.collection_type = "TILE"
        tile_props.tile_size = (self.tile_x, self.tile_y, self.tile_z)
        tile_props.base_size = (self.base_x, self.base_y, self.base_z)

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        layout.prop(self, 'tile_material_1')
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')
        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(self, 'tile_x')
        row.prop(self, 'tile_y')
        row.prop(self, 'tile_z')

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


class MT_OT_Make_Openlock_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK straight base."""

    bl_idname = "object.make_openlock_straight_base"
    bl_label = "Straight Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_openlock_base(self, tile_props)
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_openlock_base(self, tile_props)
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain straight wall core."""

    bl_idname = "object.make_plain_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "STRAIGHT_WALL_CORE"

    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_wall_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock straight wall core."""

    bl_idname = "object.make_openlock_straight_wall_core"
    bl_label = "Straight Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_WALL_CORE"

    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]
        spawn_openlock_wall_cores(self, tile_props, base)
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

    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        create_plain_rect_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Straight_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock straight floor core."""

    bl_idname = "object.make_openlock_straight_floor_core"
    bl_label = "Straight Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "STRAIGHT_FLOOR_CORE"

    base_name: StringProperty()

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


def spawn_plain_wall_cores(self, tile_props):
    """Spawn plain Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    preview_core = spawn_wall_core(self, tile_props)
    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        preview_core,
        tile_props,
        textured_vertex_groups)
    return preview_core


def spawn_openlock_wall_cores(self, tile_props, base):
    """Spawn OpenLOCK core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        base (bpy.types.Object): tile base

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_wall_core(self, tile_props)

    wall_cutters = spawn_openlock_wall_cutters(
        core,
        tile_props)

    if tile_props.tile_size[0] > 1:
        top_pegs = spawn_openlock_top_pegs(
            core,
            tile_props)

        set_bool_obj_props(top_pegs, base, tile_props, 'UNION')
        set_bool_props(top_pegs, core, 'UNION')

    for wall_cutter in wall_cutters:
        set_bool_obj_props(wall_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(wall_cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    convert_to_displacement_core(
        core,
        tile_props,
        textured_vertex_groups)

    return core


def spawn_wall_core(self, tile_props):
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

    if tile_props.wall_position == 'CENTER':
        # move core so centred, move up so on top of base and set origin to world origin
        core.location = (
            core.location[0],
            core.location[1] + (base_size[1] - tile_size[1]) / 2,
            cursor_start_loc[2] + base_size[2])
    elif tile_props.wall_position == 'SIDE':
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

    peg = load_openlock_top_peg(tile_props)

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 0.505
    array_mod.fit_type = 'FIXED_COUNT'
    array_mod.count = 2

    core_location = core.location.copy()

    if tile_props.wall_position == 'CENTER':
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

    elif tile_props.wall_position == 'SIDE':
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


def spawn_openlock_wall_cutters(core, tile_props):
    """Create the cutters for the wall and position them correctly."""
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
    if tile_props.wall_position == 'CENTER':
        left_cutter_bottom.location = [
            front_left[0],
            front_left[1] + (base_size[1] / 2),
            front_left[2] + 0.63]
    elif tile_props.wall_position == 'SIDE':
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

    if tile_props.wall_position == 'CENTER':
        # move cutter to bottom front right corner then up by 0.63 inches
        right_cutter_bottom.location = [
            front_right[0],
            front_right[1] + (base_size[1] / 2),
            front_right[2] + 0.63]
    elif tile_props.wall_position == 'SIDE':
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


def create_plain_rect_floor_cores(self, tile_props):
    """Create preview and displacement cores.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_floor_core(self, tile_props)
    textured_vertex_groups = ['Top']

    convert_to_displacement_core(
        preview_core,
        tile_props,
        textured_vertex_groups)

    bpy.context.view_layer.objects.active = preview_core

    return preview_core


def spawn_floor_core(self, tile_props):
    """Spawn the core (top part) of a floor tile.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile core
    """
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    core_size = [
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]]
    tile_name = tile_props.tile_name
    native_subdivisions = (
        get_subdivs(tile_props.subdivision_density, core_size))

    core = draw_rectangular_floor_core(
        core_size,
        native_subdivisions)

    core.name = tile_name + '.floor_core'
    add_object_to_collection(core, tile_name)

    core.location[2] = core.location[2] + base_size[2]

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
    bpy.context.view_layer.objects.active = core

    return core


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


def spawn_openlock_base(self, tile_props):
    """Spawn an openlock base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    base = spawn_plain_base(tile_props)
    slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    clip_cutters = spawn_openlock_base_clip_cutters(base, tile_props)

    for clip_cutter in clip_cutters:
        set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    mode('OBJECT')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(base, tile_props, offset=0.236):
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

    if base_dims[0] < 1 or base_dims[1] < 1:
        # work out bool size X from base size, y and z are constants.
        bool_size = [
            base_dims[0] - (offset * 2),
            0.197,
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
        a_array.fit_length = base.dimensions[1] - 1.014

        b_array = cutter_b.modifiers['Array']
        b_array.fit_length = base.dimensions[0] - 1.014

        c_array = cutter_c.modifiers['Array']
        c_array.fit_length = base.dimensions[0] - 1.014

        d_array = cutter_d.modifiers['Array']
        d_array.fit_length = base.dimensions[1] - 1.014

        cutter_d.location = (
            base_location[0] + 0.24,
            base_location[1] + 0.24,
            base_location[2] + 0.24)

        return cutter_d


def spawn_openlock_base_clip_cutters(base, tile_props):
    """Make cutters for the openlock base clips.

    Args:
        base (bpy.types.Object): tile base
        tile_props (mt_tile_props): tile properties

    Returns:
        list[bpy.types.Object]

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

    # Special case if base is small
    if base.dimensions[1] < 1:
        clip_cutter.location = (
            base_location[0] + 0.5,
            base_location[1] + 0.25,
            base_location[2])

        array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_props.base_size[0] - 1

        clip_cutter.name = 'Clip Cutter.' + base.name
        return [clip_cutter]

    clip_cutter.name = 'Y Neg Clip.' + base.name
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
    clip_cutter2.name = 'X Pos Clip.' + base.name
    clip_cutter2.data = clip_cutter2.data.copy()

    add_object_to_collection(clip_cutter2, tile_props.tile_name)
    clip_cutter2.rotation_euler = (0, 0, radians(90))

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
    clip_cutter3.name = 'Y Pos Clip.' + base.name
    clip_cutter3.data = clip_cutter3.data.copy()
    add_object_to_collection(clip_cutter3, tile_props.tile_name)

    clip_cutter3.rotation_euler = (0, 0, radians(180))

    clip_cutter3.location = (
        clip_cutter.location[0] + base.dimensions[0] - 1,
        clip_cutter.location[1] + base.dimensions[1] - 0.5,
        clip_cutter.location[2]
    )
    array_mod3 = clip_cutter3.modifiers['Array']
    array_mod3.fit_type = 'FIT_LENGTH'
    array_mod3.fit_length = base.dimensions[0] - 1

    clip_cutter4 = clip_cutter2.copy()
    clip_cutter4.name = 'X Neg Clip.' + base.name
    clip_cutter4.data = clip_cutter4.data.copy()
    add_object_to_collection(clip_cutter4, tile_props.tile_name)

    clip_cutter4.rotation_euler = (0, 0, radians(-90))

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
