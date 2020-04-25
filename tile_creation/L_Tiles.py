import os
from math import radians
import bpy
import bmesh
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group)
from .. lib.utils.utils import mode, vectors_are_close
from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    deselect_all,
    select)
from .. lib.turtle.scripts.L_tile import (
    draw_corner_3D,
    draw_corner_wall_core,
    calculate_corner_wall_triangles,
    move_cursor_to_wall_start)
from . create_tile import MT_Tile


# MIXIN
class MT_L_Tile:
    def create_plain_base(self, tile_props):
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle
        thickness = tile_props.base_size[1]
        height = tile_props.base_size[2]

        triangles = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            thickness,
            angle)

        base = draw_corner_3D(triangles, angle, thickness, height)

        base.name = tile_props.tile_name + '.base'
        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base

    def create_openlock_base(self, tile_props):
        tile_props.base_size = Vector((1, 0.5, 0.2755))
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle
        thickness = tile_props.base_size[1]

        base = self.create_plain_base(tile_props)

        base_triangles = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            thickness,
            angle)

        slot_cutter = self.create_openlock_base_slot_cutter(tile_props)

        slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
        slot_boolean.operation = 'DIFFERENCE'
        slot_boolean.object = slot_cutter
        slot_cutter.parent = base
        slot_cutter.display_type = 'BOUNDS'
        slot_cutter.hide_viewport = True

        # clip cutters - leg 1
        leg_len = base_triangles['a_adj']
        corner_loc = base.location
        clip_cutter_1 = self.create_openlock_base_clip_cutter(leg_len, corner_loc, 0.25, tile_props)
        select(clip_cutter_1.name)
        bpy.ops.transform.rotate(
            value=radians(tile_props.angle - 90),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=corner_loc)

        # clip cutters - leg 2
        leg_len = base_triangles['c_adj']
        corner_loc = base.location
        clip_cutter_2 = self.create_openlock_base_clip_cutter(
            leg_len,
            corner_loc,
            -0.25,
            tile_props)
        select(clip_cutter_2.name)
        bpy.ops.transform.mirror(constraint_axis=(False, True, False))
        bpy.ops.transform.rotate(
            value=radians(-90),
            orient_axis='Z',
            orient_type='GLOBAL',
            center_override=corner_loc)

        cutters = [clip_cutter_1, clip_cutter_2]
        for cutter in cutters:
            cutter_boolean = base.modifiers.new(cutter.name, 'BOOLEAN')
            cutter_boolean.operation = 'DIFFERENCE'
            cutter_boolean.object = cutter
            cutter.parent = base
            cutter.display_type = 'WIRE'
            cutter.hide_viewport = True

        deselect_all()

        bpy.context.scene.cursor.location = (0, 0, 0)

        return base

    def create_openlock_base_clip_cutter(
            self,
            leg_len,
            corner_loc,
            offset,
            tile_props):

        mode('OBJECT')
        # load cutter
        # Get cutter
        deselect_all()
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
            corner_loc[0] + 0.5,
            corner_loc[1] + offset,
            corner_loc[2]
        ))

        array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = leg_len - 1

        return clip_cutter

    def create_openlock_base_slot_cutter(self, tile_props):
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle

        face_dist = 0.233
        slot_width = 0.197
        slot_height = 0.25
        end_dist = 0.236  # distance of slot from base end

        cutter_triangles_1 = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            face_dist,
            angle)

        # reuse method we use to work out where to start our wall
        move_cursor_to_wall_start(
            cutter_triangles_1,
            angle,
            face_dist,
            -0.01)

        cutter_x_leg = cutter_triangles_1['b_adj'] - end_dist
        cutter_y_leg = cutter_triangles_1['d_adj'] - end_dist

        # work out dimensions of cutter
        cutter_triangles_2 = calculate_corner_wall_triangles(
            cutter_x_leg,
            cutter_y_leg,
            slot_width,
            angle
        )

        cutter = draw_corner_3D(
            cutter_triangles_2,
            angle,
            slot_width,
            slot_height)

        cutter.name = tile_props.tile_name + '.base.cutter'

        return cutter


class MT_L_Floor(MT_L_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_L_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_L_Tile.create_openlock_base(self, tile_props)
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
        textured_vertex_groups = ['Leg 1 Top', 'Leg 2 Top']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        preview_core = self.create_plain_cores(base, tile_props)
        return preview_core

    def create_core(self, tile_props):
        base_thickness = tile_props.base_size[1]
        core_thickness = tile_props.tile_size[1]
        base_height = tile_props.base_size[2]
        floor_height = tile_props.tile_size[2]
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle
        native_subdivisions = (
            tile_props.leg_1_native_subdivisions,
            tile_props.leg_2_native_subdivisions,
            tile_props.width_native_subdivisions,
            tile_props.z_native_subdivisions)
        thickness_diff = base_thickness - core_thickness

        # first work out where we're going to start drawing our wall
        # from, taking into account the difference in thickness
        # between the base and wall and how long our legs will be
        core_triangles_1 = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            thickness_diff / 2,
            angle)

        move_cursor_to_wall_start(
            core_triangles_1,
            angle,
            thickness_diff / 2,
            base_height)

        core_x_leg = core_triangles_1['b_adj']
        core_y_leg = core_triangles_1['d_adj']

        # work out dimensions of core
        core_triangles_2 = calculate_corner_wall_triangles(
            core_x_leg,
            core_y_leg,
            core_thickness,
            angle)

        # store the vertex locations for turning
        # into vert groups as we draw outline
        core, vert_locs = draw_corner_wall_core(
            core_triangles_2,
            angle,
            core_thickness,
            floor_height - base_height,
            native_subdivisions
        )

        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        # create vert groups
        corner_floor_to_vert_groups(core, vert_locs, native_subdivisions)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        mode('OBJECT')
        bpy.ops.uv.smart_project(ctx, island_margin=0.05)
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        return core


class MT_L_Wall(MT_L_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_L_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_L_Tile.create_openlock_base(self, tile_props)
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
        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 2 Outer', 'Leg 2 Inner']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size = Vector((
            tile_props.tile_size[0],
            0.3149,
            tile_props.tile_size[2]))

        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 2 Outer', 'Leg 2 Inner']

        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)

        cutters = self.create_openlock_wall_cutters(preview_core, tile_props)
        left_cutters = [cutters[0], cutters[1]]
        right_cutters = [cutters[2], cutters[3]]

        deselect_all()
        cursor = bpy.context.scene.cursor

        for cutter in right_cutters:
            cutter.location = (
                cutter.location[0] + tile_props.leg_1_len - 2,
                cutter.location[1],
                cutter.location[2])
            select(cutter.name)
        bpy.ops.transform.rotate(
            value=radians(tile_props.angle - 90),
            orient_axis='Z',
            center_override=cursor.location)

        deselect_all()

        for cutter in left_cutters:
            cutter.location = (
                cutter.location[0] + (tile_props.base_size[1] / 2),
                cutter.location[1] + tile_props.leg_2_len - (tile_props.base_size[1] / 2),
                cutter.location[2])
            cutter.rotation_euler = (0, 0, radians(-90))

        cores = [preview_core, displacement_core]

        for cutter in cutters:
            cutter.parent = base
            cutter.display_type = 'WIRE'
            cutter.hide_viewport = True
            obj_props = cutter.mt_object_props
            obj_props.is_mt_object = True
            obj_props.tile_name = tile_props.tile_name
            obj_props.geometry_type = 'CUTTER'

            for core in cores:
                cutter_bool = core.modifiers.new(cutter.name + '.bool', 'BOOLEAN')
                cutter_bool.operation = 'DIFFERENCE'
                cutter_bool.object = cutter

                # add cutters to object's mt_cutters_collection
                # so we can activate and deactivate them when necessary
                item = core.mt_object_props.cutters_collection.add()
                item.name = cutter.name
                item.value = True
                item.parent = core.name

        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        displacement_core.hide_viewport = True
        bpy.context.scene.cursor.location = (0, 0, 0)

        return preview_core

    def create_core(self, tile_props):
        base_thickness = tile_props.base_size[1]
        wall_thickness = tile_props.tile_size[1]
        base_height = tile_props.base_size[2]
        wall_height = tile_props.tile_size[2]
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle
        native_subdivisions = (
            tile_props.leg_1_native_subdivisions,
            tile_props.leg_2_native_subdivisions,
            tile_props.width_native_subdivisions,
            tile_props.z_native_subdivisions)
        thickness_diff = base_thickness - wall_thickness

        # first work out where we're going to start drawing our wall
        # from, taking into account the difference in thickness
        # between the base and wall and how long our legs will be
        core_triangles_1 = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            thickness_diff / 2,
            angle)

        move_cursor_to_wall_start(
            core_triangles_1,
            angle,
            thickness_diff / 2,
            base_height)

        core_x_leg = core_triangles_1['b_adj']
        core_y_leg = core_triangles_1['d_adj']

        # work out dimensions of core
        core_triangles_2 = calculate_corner_wall_triangles(
            core_x_leg,
            core_y_leg,
            wall_thickness,
            angle)

        # store the vertex locations for turning
        # into vert groups as we draw outline
        core, vert_locs = draw_corner_wall_core(
            core_triangles_2,
            angle,
            wall_thickness,
            wall_height - base_height,
            native_subdivisions
        )

        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        # create vert groups
        corner_wall_to_vert_groups(core, vert_locs, native_subdivisions)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        mode('OBJECT')
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.uv.smart_project(ctx, island_margin=0.01)

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
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


def select_verts_by_vert_coords(bm, vert_coords):
    for v in bm.verts:
        if v.co in vert_coords:
            v.select = True
    bmesh.update_edit_mesh(bpy.context.object.data)


def corner_wall_to_vert_groups(obj, vert_locs, native_subdivisions):
    """
    Creates vertex groups out of passed in corner wall
    and locations of bottom verts
    """
    select(obj.name)
    mode('EDIT')
    deselect_all()

    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]
    }

    # make vertex groups
    obj.vertex_groups.new(name='Leg 1 End')
    obj.vertex_groups.new(name='Leg 2 End')
    obj.vertex_groups.new(name='Leg 1 Inner')
    obj.vertex_groups.new(name='Leg 2 Inner')
    obj.vertex_groups.new(name='Leg 1 Outer')
    obj.vertex_groups.new(name='Leg 2 Outer')
    obj.vertex_groups.new(name='Leg 1 Top')
    obj.vertex_groups.new(name='Leg 2 Top')
    obj.vertex_groups.new(name='Leg 1 Bottom')
    obj.vertex_groups.new(name='Leg 2 Bottom')

    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()

    # Inner and outer faces
    groups = ('Leg 1 Outer', 'Leg 2 Outer', 'Leg 1 Inner', 'Leg 2 Inner')

    for vert_group in groups:
        for v in bm.verts:
            v.select = False

        bpy.ops.object.vertex_group_set_active(ctx, group=vert_group)
        vert_coords = vert_locs[vert_group].copy()
        subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[3]

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break

        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord


        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break

        i = 0
        while i <= native_subdivisions[3]:
            for index, coord in enumerate(vert_coords):
                vert_coords[index] = Vector((0, 0, subdiv_dist)) + coord

            for coord in vert_coords:
                for v in bm.verts:
                    if (vectors_are_close(v.co, coord, 0.0001)):
                        v.select = True
                        break
            i += 1

        bpy.ops.object.vertex_group_assign(ctx)

    # Ends
    groups = ('Leg 1 End', 'Leg 2 End')

    for vert_group in groups:
        for v in bm.verts:
            v.select = False

        bpy.ops.object.vertex_group_set_active(ctx, group=vert_group)
        vert_coords = vert_locs[vert_group].copy()
        subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[3]

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        for v in bm.verts:
            v.select = False

        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        i = 0
        while i < native_subdivisions[3]:
            for v in bm.verts:
                v.select = False

            for index, coord in enumerate(vert_coords):
                vert_coords[index] = Vector((0, 0, subdiv_dist)) + coord

            for coord in vert_coords:
                for v in bm.verts:
                    if (vectors_are_close(v.co, coord, 0.0001)):
                        v.select = True
                        break
            bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
            bpy.ops.object.vertex_group_assign(ctx)

            i += 1

        for v in bm.verts:
            v.select = False
        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)


    # Leg 1 bottom
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 1 Bottom')
    inner_vert_locs = vert_locs['Leg 1 Inner'][::-1]
    outer_vert_locs = vert_locs['Leg 1 Outer']

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0001):
                v.select = True
                break

        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0001):
                v.select = True
                break

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1


    # Leg 2 bottom
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Bottom')
    inner_vert_locs = vert_locs['Leg 2 Inner'][::-1]
    outer_vert_locs = vert_locs['Leg 2 Outer']

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if (vectors_are_close(v.co, inner_vert_locs[i], 0.0001)):
                v.select = True
                break

        for v in bm.verts:
            if (vectors_are_close(v.co, outer_vert_locs[i], 0.0001)):
                v.select = True
                break

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        for v in bm.verts:
            v.select = False

        i += 1

    # leg 1 top
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 1 Top')

    inner_vert_locs = vert_locs['Leg 1 Inner'][::-1].copy()
    outer_vert_locs = vert_locs['Leg 1 Outer'].copy()

    for index, coord in enumerate(inner_vert_locs):
        inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for index, coord in enumerate(outer_vert_locs):
        outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0001):
                v.select = True

        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0001):
                v.select = True

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1

    # leg 2 top
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Top')

    inner_vert_locs = vert_locs['Leg 2 Inner'][::-1].copy()
    outer_vert_locs = vert_locs['Leg 2 Outer'].copy()

    for index, coord in enumerate(inner_vert_locs):
        inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for index, coord in enumerate(outer_vert_locs):
        outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0001):
                v.select = True

        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0001):
                v.select = True

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1

    bmesh.update_edit_mesh(bpy.context.object.data)

    mode('OBJECT')


def corner_floor_to_vert_groups(obj, vert_locs, native_subdivisions):
    """
    Creates vertex groups out of passed in corner floor
    and locations of bottom verts
    """
    select(obj.name)
    mode('EDIT')
    deselect_all()

    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]
    }

    # make vertex groups
    obj.vertex_groups.new(name='Leg 1 End')
    obj.vertex_groups.new(name='Leg 2 End')
    obj.vertex_groups.new(name='Leg 1 Inner')
    obj.vertex_groups.new(name='Leg 2 Inner')
    obj.vertex_groups.new(name='Leg 1 Outer')
    obj.vertex_groups.new(name='Leg 2 Outer')
    obj.vertex_groups.new(name='Leg 1 Top')
    obj.vertex_groups.new(name='Leg 2 Top')
    obj.vertex_groups.new(name='Leg 1 Bottom')
    obj.vertex_groups.new(name='Leg 2 Bottom')

    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()

    # Inner and outer faces
    groups = ('Leg 1 Outer', 'Leg 2 Outer', 'Leg 1 Inner', 'Leg 2 Inner')

    for vert_group in groups:
        for v in bm.verts:
            v.select = False

        bpy.ops.object.vertex_group_set_active(ctx, group=vert_group)
        vert_coords = vert_locs[vert_group].copy()
        subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[3]

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break

        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord


        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break

        i = 0
        while i <= native_subdivisions[3]:
            for index, coord in enumerate(vert_coords):
                vert_coords[index] = Vector((0, 0, subdiv_dist)) + coord

            for coord in vert_coords:
                for v in bm.verts:
                    if (vectors_are_close(v.co, coord, 0.0001)):
                        v.select = True
                        break
            i += 1

        bpy.ops.object.vertex_group_assign(ctx)

    # Ends
    groups = ('Leg 1 End', 'Leg 2 End')

    for vert_group in groups:
        for v in bm.verts:
            v.select = False

        bpy.ops.object.vertex_group_set_active(ctx, group=vert_group)
        vert_coords = vert_locs[vert_group].copy()
        subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[3]

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        for v in bm.verts:
            v.select = False

        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        i = 0
        while i < native_subdivisions[3]:
            for v in bm.verts:
                v.select = False

            for index, coord in enumerate(vert_coords):
                vert_coords[index] = Vector((0, 0, subdiv_dist)) + coord

            for coord in vert_coords:
                for v in bm.verts:
                    if (vectors_are_close(v.co, coord, 0.0001)):
                        v.select = True
                        break
            bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
            bpy.ops.object.vertex_group_assign(ctx)

            i += 1

        for v in bm.verts:
            v.select = False
        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord

        for coord in vert_coords:
            for v in bm.verts:
                if (vectors_are_close(v.co, coord, 0.0001)):
                    v.select = True
                    break
        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)


    # Leg 1 bottom
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 1 Bottom')
    inner_vert_locs = vert_locs['Leg 1 Inner'][::-1]
    outer_vert_locs = vert_locs['Leg 1 Outer']

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0001):
                v.select = True
                break

        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0001):
                v.select = True
                break

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1


    # Leg 2 bottom
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Bottom')
    inner_vert_locs = vert_locs['Leg 2 Inner'][::-1]
    outer_vert_locs = vert_locs['Leg 2 Outer']

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if (vectors_are_close(v.co, inner_vert_locs[i], 0.0001)):
                v.select = True
                break

        for v in bm.verts:
            if (vectors_are_close(v.co, outer_vert_locs[i], 0.0001)):
                v.select = True
                break

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)

        for v in bm.verts:
            v.select = False

        i += 1

    # leg 1 top
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 1 Top')

    inner_vert_locs = vert_locs['Leg 1 Inner'][::-1].copy()
    outer_vert_locs = vert_locs['Leg 1 Outer'].copy()

    for index, coord in enumerate(inner_vert_locs):
        inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for index, coord in enumerate(outer_vert_locs):
        outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if (vectors_are_close(v.co, inner_vert_locs[i], 0.0005)):
                v.select = True
                break

        for v in bm.verts:
            if (vectors_are_close(v.co, outer_vert_locs[i], 0.0005)):
                v.select = True
                break

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1

    # leg 2 top
    bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Top')

    inner_vert_locs = vert_locs['Leg 2 Inner'][::-1].copy()
    outer_vert_locs = vert_locs['Leg 2 Outer'].copy()

    for index, coord in enumerate(inner_vert_locs):
        inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for index, coord in enumerate(outer_vert_locs):
        outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(outer_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0005):
                v.select = True

        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0005):
                v.select = True

        bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign(ctx)
        for v in bm.verts:
            v.select = False
        i += 1

    bmesh.update_edit_mesh(bpy.context.object.data)

    mode('OBJECT')

    # remove side verts from top groups
    leg_1_side_groups = ['Leg 1 Inner', 'Leg 1 Outer', 'Leg 1 End']
    leg_1_side_vert_indices = []

    for group in leg_1_side_groups:
        verts = get_vert_indexes_in_vert_group(group, obj)
        leg_1_side_vert_indices.extend(verts)

    remove_verts_from_group('Leg 1 Top', obj, leg_1_side_vert_indices)

    leg_2_side_groups = ['Leg 2 Inner', 'Leg 2 Outer', 'Leg 2 End']
    leg_2_side_vert_indices = []

    for group in leg_2_side_groups:
        verts = get_vert_indexes_in_vert_group(group, obj)
        leg_2_side_vert_indices.extend(verts)

    remove_verts_from_group('Leg 2 Top', obj, leg_2_side_vert_indices)
