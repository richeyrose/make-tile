import os
from math import radians, pi, modf
from mathutils import Vector
import bpy
from bpy.types import Operator, Panel
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.openlock_curved_wall_base import draw_openlock_curved_base
from .. lib.turtle.scripts.straight_tile import draw_straight_wall_core
from .. lib.utils.selection import (
    deselect_all,
    select,
    activate)
from .. lib.utils.utils import (
    add_circle_array,
    get_all_subclasses)
from .create_tile import (
    create_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab)
from . Rectangular_Tiles import make_rect_floor_vert_groups
from . Straight_Tiles import straight_wall_to_vert_groups

class MT_OT_Make_Curved_Floor_Tile(MT_Tile_Generator, Operator):
    """Create a Curved Floor Tile"""
    bl_idname = "object.make_curved_floor"
    bl_label = "Curved Floor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

# MIXIN #
class MT_Curved_Tile:
    def create_plain_base(self, tile_props):
        radius = tile_props.base_radius
        segments = tile_props.curve_native_subdivisions
        angle = tile_props.degrees_of_arc
        height = tile_props.base_size[2]
        width = tile_props.base_size[1]

        t = bpy.ops.turtle

        t.add_turtle()
        t.pd()
        t.arc(r=radius, d=angle, s=segments)
        t.arc(r=radius + width, d=angle, s=segments)
        t.select_all()
        t.bridge()
        t.pd()
        t.select_all()
        t.up(d=height)
        t.home()
        bpy.ops.object.editmode_toggle()

        base = bpy.context.object
        base.name = tile_props.tile_name + '.base'

        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base

    def create_openlock_base(self, tile_props):
        radius = tile_props.base_radius
        segments = tile_props.curve_native_subdivisions
        angle = tile_props.degrees_of_arc
        tile_props.base_size[2] = 0.2755
        tile_props.base_size[1] = 0.5
        clip_side = tile_props.base_socket_side

        base = draw_openlock_curved_base(
            radius,
            segments,
            angle,
            tile_props.base_size[2],
            clip_side)
        self.create_openlock_base_clip_cutter(base, tile_props)

        base.name = tile_props.tile_name + '.base'
        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base

    def create_openlock_base_clip_cutter(self, base, tile_props):
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
        radius = tile_props.base_radius + (tile_props.base_size[1] / 2)

        clip_cutter.location[1] = radius

        if clip_side == 'OUTER':
            clip_cutter.rotation_euler[2] = radians(180)

        num_cutters = modf((tile_props.degrees_of_arc - 22.5) / 22.5)
        circle_center = cursor_orig_loc

        if num_cutters[1] == 1:
            initial_rot = (-tile_props.degrees_of_arc / 2)

        else:
            initial_rot = -22.5

        bpy.ops.transform.rotate(
            value=radians(initial_rot),
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

        empty.hide_viewport = True

        clip_cutter.parent = base
        clip_cutter.display_type = 'WIRE'
        clip_cutter.hide_viewport = True
        clip_cutter_bool = base.modifiers.new('Base Cutter', 'BOOLEAN')
        clip_cutter_bool.operation = 'DIFFERENCE'
        clip_cutter_bool.object = clip_cutter

        obj_props = clip_cutter.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        obj_props.geometry_type = 'CUTTER'

        return clip_cutter


class MT_Curved_Floor_Tile(MT_Curved_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_Curved_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_Curved_Tile.create_openlock_base(self, tile_props)
        return base

    def create_empty_base(self, tile_props):
        tile_props.base_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0)
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
        tile_props.tile_size[1] = 0.5
        return self.create_plain_cores(base, tile_props)

    def create_core(self, tile_props):
        angle = tile_props.degrees_of_arc
        radius = tile_props.base_radius
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
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        tile_props.tile_size[0] = wall_length
        make_rect_floor_vert_groups(core)

        core.location = (
            core.location[0],
            core.location[1] + tile_props.base_radius,
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


class MT_Curved_Wall_Tile(MT_Curved_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_Curved_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_Curved_Tile.create_openlock_base(self, tile_props)
        return base

    def create_empty_base(self, tile_props):
        tile_props.base_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0)
        base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
        add_object_to_collection(base, tile_props.tile_name)
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
        tile_props.tile_size[1] = 0.3149

        offset = (tile_props.base_size[1] - tile_props.tile_size[1]) / 2
        tile_props.wall_radius = tile_props.base_radius + offset
        textured_vertex_groups = ['Front', 'Back']

        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)

        cores = [preview_core, displacement_core]

        cutters = self.create_openlock_wall_cutters(
            preview_core,
            base.location,
            tile_props)

        for cutter in cutters:
            obj_props = cutter.mt_object_props
            cutter.parent = base
            cutter.display_type = 'WIRE'
            cutter.hide_viewport = True
            obj_props.is_mt_object = True
            obj_props.tile_name = tile_props.tile_name
            obj_props.geometrt_type = 'CUTTER'

            for core in cores:
                cutter_bool = core.modifiers.new(cutter.name + '.bool', 'BOOLEAN')
                cutter_bool.operation = 'DIFFERENCE'
                cutter_bool.object = cutter
                cutter_bool.show_render = False

                # add cutters to object's mt_cutters_collection
                # so we can activate and deactivate them when necessary
                item = core.mt_object_props.cutters_collection.add()
                item.name = cutter.name
                item.value = True
                item.parent = core.name
        displacement_core.hide_viewport = True

        return preview_core

    def create_core(self, tile_props):
        angle = tile_props.degrees_of_arc
        radius = tile_props.wall_radius
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
            'selected_objects': [core]
        }

        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        straight_wall_to_vert_groups(core)

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

    def create_openlock_wall_cutters(self, core, base_location, tile_props):
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
            value=radians(-tile_props.degrees_of_arc),
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
