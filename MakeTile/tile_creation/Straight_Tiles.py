import os
from math import radians

import bpy
from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    StringProperty)

from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection)

from ..lib.bmturtle.scripts import (
    draw_straight_wall_core,
    draw_cuboid,
    draw_rectangular_floor_core)

from .create_tile import (
    spawn_empty_base,
    convert_to_displacement_core,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    add_subsurf_modifier)
'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


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

        if scene_props.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(scene_props, 'base_socket_type')

        layout.label(text="Materials")
        if scene_props.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.prop(scene_props, 'floor_material')
        layout.prop(scene_props, 'wall_material')

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

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

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

        if scene_props.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(scene_props, 'base_socket_type')

        layout.label(text="Materials")
        layout.prop(scene_props, 'floor_material')

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

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Straight_Wall_Tile(Operator, MT_Tile_Generator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "STRAIGHT_WALL"

    # S Wall Props
    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base."),
            ("OUTER", "Outer", "Wall is an outer wall.")],
        default="CENTER")

    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

    wall_material: EnumProperty(
        items=create_material_enums,
        name="Wall Material")

    def exec(self, context):
        base_blueprint = self.base_blueprint
        wall_blueprint = self.main_part_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint == 'NONE':
            base = spawn_empty_base(tile_props)
        elif base_blueprint in ['PLAIN', 'PLAIN_S_WALL']:
            base = spawn_plain_base(self, tile_props)
        elif base_blueprint in ['OPENLOCK', 'OPENLOCK_S_WALL']:
            base = spawn_openlock_base(self, tile_props)

        if wall_blueprint == 'NONE':
            wall_core = None
        elif wall_blueprint == 'PLAIN':
            wall_core = spawn_plain_wall_cores(self, tile_props)
        elif wall_blueprint == 'OPENLOCK':
            wall_core = spawn_openlock_wall_cores(self, tile_props, base)

        if base_blueprint in {'OPENLOCK_S_WALL', 'PLAIN_S_WALL'}:
            # We temporarily override tile_props.base_size to generate floor core for S-Tiles.
            # It is easier to do it this way as the PropertyGroup.copy() method produces a dict
            orig_tile_size = []
            for c, v in enumerate(tile_props.tile_size):
                orig_tile_size.append(v)

            # correct for displacement material
            if self.wall_position in ['OUTER', 'SIDE']:
                tile_props.base_size[1] = tile_props.base_size[1] - 0.09

            context.collection.mt_tile_props.tile_size = (
                tile_props.base_size[0],
                tile_props.base_size[1],
                tile_props.base_size[2] + self.floor_thickness)
            floor_core = create_plain_rect_floor_cores(self, tile_props)
            tile_props.tile_size = orig_tile_size
            self.finalise_tile(context, base, wall_core, floor_core)
        else:
            self.finalise_tile(context, base, wall_core)
        return {'FINISHED'}

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}
        return self.exec(context)

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

        layout.label(text="Blueprints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')

        if self.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(self, 'base_socket_type')

        layout.label(text="Materials")
        if self.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.prop(self, 'floor_material')
        layout.prop(self, 'wall_material')

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

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


class MT_OT_Make_Rect_Floor_Tile(Operator, MT_Tile_Generator):
    """Operator. Generates a rectangular floor tile with a customisable base and main part."""

    bl_idname = "object.make_rect_floor"
    bl_label = "Rectangular Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "RECT_FLOOR"

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}

        self.exec(context)
        # profile.dump_stats(splitext(__file__)[0] + '.prof')
        return {'FINISHED'}

    # @profile
    def exec(self, context):
        base_blueprint = self.base_blueprint
        core_blueprint = self.main_part_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint == 'NONE':
            base = spawn_empty_base(tile_props)
        elif base_blueprint == 'OPENLOCK':
            base = spawn_openlock_base(self, tile_props)
        elif base_blueprint == 'PLAIN':
            base = spawn_plain_base(self, tile_props)

        if core_blueprint == 'NONE':
            core = None
        else:
            core = create_plain_rect_floor_cores(self, tile_props)
        self.finalise_tile(context, base, core)

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

        layout.label(text="Blueprints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')

        if self.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(self, 'base_socket_type')

        layout.label(text="Materials")
        layout.prop(self, 'floor_material')

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

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")

def spawn_plain_wall_cores(self, tile_props):
    """Spawn plain Core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    core = spawn_wall_core(self, tile_props)
    subsurf = add_subsurf_modifier(core)
    textured_vertex_groups = ['Front', 'Back']
    material = tile_props.wall_material

    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)
    return core


def spawn_openlock_wall_cores(self, tile_props, base):
    """Spawn OpenLOCK core.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        base (bpy.types.Object): tile base

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_wall_core(self, tile_props)
    subsurf = add_subsurf_modifier(core)

    wall_cutters = spawn_openlock_wall_cutters(
        core,
        base,
        tile_props)

    if tile_props.tile_size[0] > 1:
        top_pegs = spawn_openlock_top_pegs(
            core,
            base,
            tile_props)

        set_bool_obj_props(top_pegs, base, tile_props, 'UNION')
        set_bool_props(top_pegs, core, 'UNION')

    for wall_cutter in wall_cutters:
        set_bool_obj_props(wall_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(wall_cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    material = tile_props.wall_material

    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    return core


def spawn_wall_core(self, tile_props):
    """Return the core (vertical) part of a straight wall tile."""
    cursor = bpy.context.scene.cursor
    cursor_start_loc = cursor.location.copy()
    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    if self.wall_position == 'OUTER':
        core_size = [s for s in tile_size]
    else:
        core_size = [
            tile_size[0],
            tile_size[1],
            tile_size[2] - base_size[2]]

    tile_name = tile_props.tile_name
    native_subdivisions = get_subdivs(
        tile_props.subdivision_density, core_size)

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
            cursor_start_loc[2] + base_size[2   ])
    elif tile_props.wall_position == 'SIDE':
        core.location = (
            core.location[0],
            core.location[1] + base_size[1] - tile_size[1] - 0.09,
            cursor_start_loc[2] + base_size[2])
    elif tile_props.wall_position == 'OUTER':
        core.location[1] = core.location[1] + base_size[1] - tile_size[1]
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_openlock_top_pegs(core, base, tile_props):
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

    # core_location = core.location.copy()
    base_location = base.location.copy()

    if tile_props.wall_position == 'CENTER':
        if tile_size[0] < 4 and tile_size[0] >= 1:
            peg.location = (
                base_location[0] + (tile_size[0] / 2) - 0.252,
                base_location[1] + (base_size[1] / 2) + 0.08,
                base_location[2] + tile_size[2])
        else:
            peg.location = (
                base_location[0] + 0.756,
                base_location[1] + (base_size[1] / 2) + 0.08,
                base_location[2] + tile_size[2])

    elif tile_props.wall_position == 'SIDE':
        if tile_size[0] < 4 and tile_size[0] >= 1:
            peg.location = (
                base_location[0] + (tile_size[0] / 2) - 0.252,
                base_location[1] + base_size[1] - 0.33,
                base_location[2] + tile_size[2])
        else:
            peg.location = (
                base_location[0] + 0.756,
                base_location[1] + base_size[1] - 0.33,
                base_location[2] + tile_size[2])
    elif tile_props.wall_position == 'OUTER':
        if tile_size[0] < 4 and tile_size[0] >= 1:
            peg.location = (
                base_location[0] + (tile_size[0] / 2) - 0.252,
                base_location[1] + base_size[1] - 0.33 + 0.09,
                base_location[2] + tile_size[2])
        else:
            peg.location = (
                base_location[0] + 0.756,
                base_location[1] + base_size[1] - 0.33 + 0.09,
                base_location[2] + tile_size[2])

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 2.017
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = tile_size[0] - 1.3
    return peg


def spawn_openlock_wall_cutters(core, base, tile_props):
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

    # core_location = core.location.copy()
    base_location = base.location.copy()

    cutters = []
    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name

    add_object_to_collection(left_cutter_bottom, tile_name)
    # get location of bottom front left corner of tile
    front_left = base_location

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
    elif tile_props.wall_position == 'OUTER':
        left_cutter_bottom.location = [
            front_left[0],
            front_left[1] + base_size[1] - (tile_size[1] / 2),
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
        base_location[0] + (tile_size[0]),
        base_location[1],
        base_location[2]]

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
    elif tile_props.wall_position == 'OUTER':
        right_cutter_bottom.location = [
            front_right[0],
            front_left[1] + base_size[1] - (tile_size[1] / 2),
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
    core = spawn_floor_core(self, tile_props)
    subsurf = add_subsurf_modifier(core)
    textured_vertex_groups = ['Top']
    material = tile_props.floor_material
    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    bpy.context.view_layer.objects.active = core

    return core


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

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core


def spawn_plain_base(self, tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    base_size = tile_props.base_size

    try:
        if self.wall_position == 'OUTER':
            base_size[1] = base_size[1] - 0.09
    except AttributeError:
        pass

    tile_name = tile_props.tile_name

    # make base
    base = draw_cuboid(base_size)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

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
    base = spawn_plain_base(self, tile_props)
    slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props)
    if slot_cutter:
        set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(slot_cutter, base, 'DIFFERENCE')

    clip_cutters = spawn_openlock_base_clip_cutters(self, base, tile_props)

    for clip_cutter in clip_cutters:
        set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

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
    base_location = base.location.copy()
    base_dims = base.dimensions.copy()

    if base_dims[0] <= 0.5:
        return False

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


def spawn_openlock_base_clip_cutters(self, base, tile_props):
    """Make cutters for the openlock base clips.

    Args:
        base (bpy.types.Object): tile base
        tile_props (mt_tile_props): tile properties

    Returns:
        list[bpy.types.Object]

    """
    base_location = base.location.copy()
    base_dims = base.dimensions

    # Prevent drawing of clip cutters if base is too small
    if base_dims[0] < 1:
        return[]

    preferences = get_prefs()
    cutter_file = self.get_base_socket_filename()
    if cutter_file:
        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes",
            "booleans",
            cutter_file)

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

        # For narrow wall bases
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

        return [clip_cutter, clip_cutter2, clip_cutter3, clip_cutter4]
    return False
