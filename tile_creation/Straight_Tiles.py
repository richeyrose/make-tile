" Contains functions for creating wall tiles """
import os
from math import radians
from mathutils import Vector
import bpy
from . create_tile import MT_Tile
from .. utils.registration import get_prefs
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.selection import select
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.utils import mode, view3d_find
from .. lib.utils.vertex_groups import straight_wall_to_vert_groups, straight_floor_to_vert_groups

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
            tile_props.base_size[0],
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

    def create_core(self, tile_props):
        '''Returns the core (vertical or top) part of a straight tile
        '''
        cursor = bpy.context.scene.cursor
        cursor_start_loc = cursor.location.copy()
        tile_size = tile_props.tile_size
        base_size = tile_props.base_size
        tile_name = tile_props.tile_name

        # make our core
        core = draw_cuboid([
            tile_size[0],
            tile_size[1],
            tile_size[2] - base_size[2]])

        core.name = tile_name + '.core'
        add_object_to_collection(core, tile_name)
        mode('OBJECT')

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
        bpy.ops.uv.smart_project(ctx, island_margin=0.05)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_name

        return core

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
        base = MT_Straight_Tile.create_openlock_base(self, tile_props)
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
        tile_props.tile_size[1] = tile_props.base_size[1]
        preview_core = self.create_plain_cores(base, tile_props)
        return preview_core

    def create_core(self, tile_props):
        '''Returns the core (top) part of a floor tile
        '''
        core = MT_Straight_Tile.create_core(self, tile_props)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=0.05)

        straight_floor_to_vert_groups(core, tile_props)

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
        # Again width is a constant for OpenLOCK tiles
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

        core = MT_Straight_Tile.create_core(self, tile_props)

        self.create_core_loops(core, tile_props, cursor_start_loc)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=0.05)

        straight_wall_to_vert_groups(core)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core

    def create_core_loops(self, core, tile_props, cursor_start_loc):
        # create loops at each side of tile which we'll use
        # to prevent materials projecting beyond edges
        base_size = tile_props.base_size
        tile_size = tile_props.tile_size

        mode('OBJECT')
        select(core.name)
        mode('EDIT')

        diff = base_size[1] - tile_size[1]
        region, rv3d, v3d, area = view3d_find(True)
        ctx = {
            'scene': bpy.context.scene,
            'region': region,
            'area': area,
            'space': v3d
        }

        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(tile_size[0] - 0.001, 0, 0),
            plane_no=(1, 0, 0))
        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(cursor_start_loc[0] + 0.001, 0, 0),
            plane_no=(1, 0, 0))
        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(0, tile_size[1] + (diff / 2) - 0.001, 0),
            plane_no=(0, 1, 0))
        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(0, cursor_start_loc[1] + (diff / 2) + 0.001, 0),
            plane_no=(0, 1, 0))
        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(0, 0, tile_size[2] - 0.01),
            plane_no=(0, 0, 1))
        bpy.ops.mesh.select_all(ctx, action='SELECT')
        bpy.ops.mesh.bisect(
            ctx,
            plane_co=(0, 0, cursor_start_loc[2] + base_size[2] + 0.001),
            plane_no=(0, 0, 1))
        mode('OBJECT')

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
