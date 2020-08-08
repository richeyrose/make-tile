import os
from math import radians
from mathutils import Vector
import bpy

from bpy.types import Operator, Panel
from . create_tile import MT_Tile
from ..ui.object_generation_panels import MT_PT_Tile_Options_Panel
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.turtle.scripts.straight_tile import draw_straight_floor_core, draw_straight_wall_core
from .. lib.utils.utils import mode
from .. lib.utils.selection import deselect_all, select_by_loc
from .Rectangular_Tiles import rect_floor_to_vert_groups
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

'''
class MT_PT_Straight_Wall_Options_Panel(Panel, MT_PT_Tile_Options_Panel):
    """Draw the tile options panel for straight wall tiles."""

    bl_idname = 'MT_PT_Straight_Wall_Options'
    bl_order = 2

    @classmethod
    def poll(cls, context):
        """Check we are in object mode."""
        return context.scene.mt_scene_props.mt_tile_type_new == "object.make_straight_wall"

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'mt_base_x')
        row.prop(scene_props, 'mt_base_y')
        row.prop(scene_props, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'mt_tile_x')
        row.prop(scene_props, 'mt_tile_y')
        row.prop(scene_props, 'mt_tile_z')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_main_part_blueprint == 'NONE':
            layout.label(text="Base Size")
            layout.prop(scene_props, 'mt_tile_x')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size:")
        row = layout.row()

        if scene_props.mt_tile_type == 'STRAIGHT_WALL':
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_z')
        else:
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_y')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_x_native_subdivisions')
        layout.prop(scene_props, 'mt_y_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')
'''

class MT_OT_Make_Plain_Straight_Wall_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a straight wall tile."""

    bl_idname = "object.make_plain_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'REGISTER', 'UNDO'}
    mt_blueprint = "PLAIN"

    def execute(self, context):
        """Execute the operator."""
        print("Make plain straight wall")
        return {'FINISHED'}


class MT_OT_Make_Openlock_Straight_Wall_Tile(MT_Tile_Generator, Operator):
    """Operator. Generates a straight wall tile."""

    bl_idname = "object.make_openlock_straight_wall"
    bl_label = "Straight Wall"
    bl_options = {'REGISTER', 'UNDO'}
    mt_blueprint = "OPENLOCK"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        original_renderer, tile_name, tiles_collection = initialise_tile_creator(context)

        create_collection('Walls', tiles_collection)
        tile_collection = bpy.data.collections.new(tile_name)
        bpy.data.collections['Walls'].children.link(tile_collection)
        activate_collection(tile_collection.name)

        tile_props = tile_collection.mt_tile_props
        create_common_tile_props(scene_props, tile_props, tile_collection)

        tile_props.tile_type = 'STRAIGHT_WALL'
        tile_props.tile_size = (scene_props.mt_tile_x, scene_props.mt_tile_y, scene_props.mt_tile_z)
        tile_props.base_size = (scene_props.mt_base_x, scene_props.mt_base_y, scene_props.mt_base_z)

        tile_props.x_native_subdivisions = scene_props.mt_x_native_subdivisions
        tile_props.y_native_subdivisions = scene_props.mt_y_native_subdivisions
        tile_props.z_native_subdivisions = scene_props.mt_z_native_subdivisions

        MT_Straight_Wall_Tile(tile_props)

        scene.render.engine = original_renderer
        return {'FINISHED'}


# MIXIN
class MT_Straight_Tile:
    def create_plain_base(self, tile_props):
        base_size = tile_props.base_size
        tile_name = tile_props.tile_name

        # make base
        base = draw_cuboid(base_size)
        base.name = tile_name + '.base'
        add_object_to_collection(base, tile_name)

        # Where possible we use the native python API rather than operators.
        # If we do use operators we override the context as this is faster
        # than selecting and deselecting objects and also lets us ignore what
        # object is selected, active etc. Not always possible to do this
        # unfortunately so sometimes we have to use selection
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

        return base

    def create_openlock_base(self, tile_props):
        '''Returns an openlock style base with clip sockets'''
        # For OpenLOCK tiles the width and height of the base are constants
        tile_props.base_size = Vector((
            tile_props.tile_size[0],
            0.5,
            0.2755))

        # make base
        base = self.create_plain_base(tile_props)

        # create the slot cutter in the bottom of the base used for stacking tiles
        slot_cutter = self.create_openlock_base_slot_cutter(base, tile_props, offset=0.236)
        slot_cutter.hide_viewport = True

        # create the clip cutters used for attaching walls to bases
        if base.dimensions[0] >= 1:
            clip_cutter = self.create_openlock_base_clip_cutter(base, tile_props)
            clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
            clip_boolean.operation = 'DIFFERENCE'
            clip_boolean.object = clip_cutter
            clip_cutter.parent = base
            clip_cutter.display_type = 'BOUNDS'
            clip_cutter.hide_viewport = True

        return base

    def create_openlock_base_slot_cutter(self, base, tile_props, offset=0.236):
        """Makes a cutter for the openlock base slot
        based on the width of the base
        """
        # get original location of object and cursor
        base_location = base.location.copy()
        base_size = tile_props.base_size

        # work out bool size X from base size, y and z are constants.
        # Correct for negative base dimensions when making curved walls
        if base_size[0] > 0:
            bool_size = [
                base_size[0] - (0.236 * 2),
                0.197,
                0.25]
        else:
            bool_size = [
                base_size[0] + (0.236 * 2),
                0.197,
                0.25]

        cutter = draw_cuboid(bool_size)
        cutter.name = tile_props.tile_name + ".slot_cutter"

        diff = base_size[0] - bool_size[0]

        cutter.location = (
            base_location[0] + diff / 2,
            base_location[1] + offset,
            base_location[2] - 0.001)

        ctx = {
            'object': cutter,
            'active_object': cutter,
            'selected_objects': [cutter]
        }

        base.select_set(False)
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        slot_boolean = base.modifiers.new(cutter.name, 'BOOLEAN')
        slot_boolean.operation = 'DIFFERENCE'
        slot_boolean.object = cutter
        cutter.parent = base
        cutter.display_type = 'BOUNDS'
        cutter.hide_viewport = True

        cutter.mt_object_props.is_mt_object = True
        cutter.mt_object_props.geometry_type = 'CUTTER'
        cutter.mt_object_props.tile_name = tile_props.tile_name

        return cutter

    def create_openlock_base_clip_cutter(self, base, tile_props):
        """Makes a cutter for the openlock base clip based
        on the width of the base and positions it correctly
        """

        mode('OBJECT')

        # get original location of cursor
        base_location = base.location.copy()

        # Get cutter
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
            base_location[0] + 0.5,
            base_location[1] + 0.25,
            base_location[2]))

        array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_props.base_size[0] - 1

        obj_props = clip_cutter.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        obj_props.geometry_type = 'CUTTER'

        return clip_cutter


class MT_Straight_Floor_Tile(MT_Straight_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        """Returns a plain base for a straight wall tile
        """
        base = MT_Straight_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        '''Returns an openlock style base with clip sockets'''

        tile_props.base_size = Vector((
            tile_props.tile_size[0],
            0.5,
            0.2755))
        return MT_Straight_Tile.create_openlock_base(self, tile_props)

    def create_empty_base(self, tile_props):
        tile_props.base_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0
        )
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        add_object_to_collection(base, tile_props.tile_name)
        return base

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['Top']

        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size = Vector((
            tile_props.tile_size[0],
            0.5,
            0.3))

        preview_core = self.create_plain_cores(base, tile_props)
        return preview_core

    def create_core(self, tile_props):
        '''Returns the core (top) part of a floor tile
        '''
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

        core = draw_straight_floor_core(
            [tile_size[0],
             tile_size[1],
             tile_size[2] - base_size[2]],
            native_subdivisions)

        core.name = tile_name + '.core'
        add_object_to_collection(core, tile_name)

        core.location = (
            core.location[0],
            core.location[1] + (base_size[1] - tile_size[1]) / 2,
            cursor_start_loc[2] + base_size[2])

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        rect_floor_to_vert_groups(core)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core


class MT_Straight_Wall_Tile(MT_Straight_Tile, MT_Tile):

    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        """Returns a plain base for a straight wall tile
        """
        base = MT_Straight_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        '''Returns an openlock style base with clip sockets'''
        if bpy.context.scene.mt_scene_props.mt_main_part_blueprint == 'OPENLOCK':
            tile_props.base_size[0] = tile_props.tile_size[0]
        base = MT_Straight_Tile.create_openlock_base(self, tile_props)
        return base

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['Front', 'Back']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        # width is a constant for OpenLOCK tiles
        tile_props.tile_size = Vector((
            tile_props.tile_size[0],
            0.3149,
            tile_props.tile_size[2]))

        textured_vertex_groups = ['Front', 'Back']

        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)

        wall_cutters = self.create_openlock_wall_cutters(
            preview_core,
            tile_props)

        cores = [preview_core, displacement_core]
        tile_name = tile_props.tile_name

        for wall_cutter in wall_cutters:
            wall_cutter.parent = base
            wall_cutter.display_type = 'BOUNDS'
            wall_cutter.hide_viewport = True
            obj_props = wall_cutter.mt_object_props
            obj_props.is_mt_object = True
            obj_props.tile_name = tile_name
            obj_props.geometry_type = 'CUTTER'

            for core in cores:
                wall_cutter_bool = core.modifiers.new(wall_cutter.name + '.bool', 'BOOLEAN')
                wall_cutter_bool.operation = 'DIFFERENCE'
                wall_cutter_bool.object = wall_cutter
                wall_cutter_bool.show_render = False

                # add cutters to object's mt_cutters_collection
                # so we can activate and deactivate them when necessary
                item = core.mt_object_props.cutters_collection.add()
                item.name = wall_cutter.name
                item.value = True
                item.parent = core.name

        displacement_core.hide_viewport = True

        return preview_core

    def create_core(self, tile_props):
        '''Returns the core (vertical) part of a wall tile
        '''

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

        core = draw_straight_wall_core(
            [tile_size[0],
             tile_size[1],
             tile_size[2] - base_size[2]],
            native_subdivisions)

        core.name = tile_name + '.core'
        add_object_to_collection(core, tile_name)

        # move core so centred, move up so on top of base and set origin to world origin
        core.location = (
            core.location[0],
            core.location[1] + (base_size[1] - tile_size[1]) / 2,
            cursor_start_loc[2] + base_size[2])

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        straight_wall_to_vert_groups(core)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core

    def create_openlock_wall_cutters(self, core, tile_props):
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
        right_cutter_top.name = 'X Pos Top.' + tile_name

        add_object_to_collection(right_cutter_top, tile_name)
        right_cutter_top.location[2] = right_cutter_top.location[2] + 0.75

        array_mod = right_cutter_top.modifiers["Array"]
        array_mod.fit_length = tile_size[2] - 1.8

        cutters.extend([right_cutter_bottom, right_cutter_top])

        return cutters


def straight_wall_to_vert_groups(obj):
    """makes a vertex group for each side of wall
    and assigns vertices to it. Corrects for displacement map distortion"""

    mode('OBJECT')
    dim = obj.dimensions / 2

    # get original location of object origin and of cursor
    obj_original_loc = obj.location.copy()
    cursor_original_loc = bpy.context.scene.cursor.location.copy()

    # set origin to center of bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # make vertex groups
    obj.vertex_groups.new(name='Left')
    obj.vertex_groups.new(name='Right')
    obj.vertex_groups.new(name='Front')
    obj.vertex_groups.new(name='Back')
    obj.vertex_groups.new(name='Top')
    obj.vertex_groups.new(name='Bottom')

    mode('EDIT')

    # select X- and assign to X-
    select_by_loc(
        lbound=[-dim[0] - 0.01, -dim[1], -dim[2] + 0.001],
        ubound=[-dim[0] + 0.01, dim[1], dim[2] - 0.001],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)

    bpy.ops.object.vertex_group_set_active(group='Left')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select X+ and assign to X+
    select_by_loc(
        lbound=[dim[0] - 0.01, -dim[1], -dim[2] + 0.001],
        ubound=[dim[0] + 0.01, dim[1], dim[2] - 0.001],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Right')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y- and assign to Y-
    select_by_loc(
        lbound=[-dim[0] + 0.001, -dim[1], -dim[2] + 0.001],
        ubound=[dim[0] - 0.001, -dim[1], dim[2] - 0.001],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Front')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Y+ and assign to Y+
    select_by_loc(
        lbound=[-dim[0] + 0.001, dim[1], -dim[2] + 0.001],
        ubound=[dim[0] - 0.001, dim[1], dim[2] - 0.001],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Back')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z- and assign to Z-
    select_by_loc(
        lbound=[-dim[0] + 0.001, -dim[1], -dim[2]],
        ubound=[dim[0] - 0.001, dim[1], -dim[2] + 0.01],
        select_mode='VERT',
        coords='LOCAL',
        buffer=0.0001,
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select Z+ and assign to Z+
    select_by_loc(
        lbound=[-dim[0] + 0.001, -dim[1], dim[2] - 0.012],
        ubound=[dim[0] - 0.001, dim[1], dim[2]],
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
