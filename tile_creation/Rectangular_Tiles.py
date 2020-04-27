import os
import math
import bpy
from mathutils import Vector
from . create_tile import MT_Tile
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.straight_tile import draw_rectangular_floor_core
from .. lib.turtle.scripts.openlock_floor_base import draw_openlock_rect_floor_base
from .. lib.utils.selection import deselect_all, select_by_loc


class MT_Rectangular_Tile:
    def create_plain_base(self, tile_props):
        base_size = tile_props.base_size
        tile_name = tile_props.tile_name

        # make base
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

        return base

    def create_openlock_base(self, tile_props):
        tile_name = tile_props.tile_name
        base_size = tile_props.base_size

        base_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            .2756)

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

        clip_cutters = self.create_openlock_base_clip_cutter(base, tile_props)

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

        return base

    def create_openlock_base_clip_cutter(self, base, tile_props):
        """Makes a cutter for the openlock base clip based
        on the width of the base and positions it correctly

        Keyword arguments:
        base -- base the cutter will be used on
        tile_name -- the tile name
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


class MT_Rectangular_Floor_Tile(MT_Rectangular_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_empty_base(self, tile_props):
        tile_props.base_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0
        )
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        add_object_to_collection(base, tile_props.tile_name)
        return base

    def create_openlock_base(self, tile_props):
        tile_props.base_size = Vector((
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0.2755))
        return MT_Rectangular_Tile.create_openlock_base(self, tile_props)

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
            tile_props.tile_size[1],
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

        rect_floor_to_vert_groups(core)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core


def rect_floor_to_vert_groups(obj):
    """makes a vertex group for each side of floor
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
