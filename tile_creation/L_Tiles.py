import os
import bpy
from math import tan, radians
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.vertex_groups import (
    corner_wall_to_vert_groups)
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    deselect_all,
    select)
from . create_tile import MT_Tile


# MIXIN
class MT_L_Tile:
    def create_plain_base(self, tile_props):
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        base_height = tile_props.base_size[2]
        angle = tile_props.angle
        base_thickness = tile_props.base_size[1]

        t = bpy.ops.turtle
        t.add_turtle()

        base_triangles = calculate_corner_wall_triangles(
            leg_1_len,
            leg_2_len,
            base_thickness,
            angle)

        vert_locs = draw_corner_outline(base_triangles, angle, base_thickness)
        t.select_all()
        bpy.ops.mesh.edge_face_add()
        t.pd()
        t.up(d=base_height)
        t.select_all()
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.mesh.quads_convert_to_tris(
            quad_method='BEAUTY',
            ngon_method='BEAUTY')
        t.pu()
        t.deselect_all()
        t.home()
        bpy.ops.object.editmode_toggle()
        base = bpy.context.object

        base.name = tile_props.tile_name + '.base'
        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base, base_triangles, vert_locs

    def create_openlock_base(self, tile_props):
        tile_props.base_size = Vector((1, 0.5, 0.2755))

        base, base_triangles, vert_locs = self.create_plain_base(tile_props)

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
        clip_cutter_2 = self.create_openlock_base_clip_cutter(leg_len, corner_loc, -0.25, tile_props)
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
        return base

    def create_core(self, tile_props):
        base_thickness = tile_props.base_size[1]
        wall_thickness = tile_props.tile_size[1]
        base_height = tile_props.base_size[2]
        wall_height = tile_props.tile_size[2]
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        angle = tile_props.angle

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
        vert_locs = draw_corner_outline(
            core_triangles_2,
            angle,
            wall_thickness)

        # fill face and extrude wall
        t = bpy.ops.turtle
        bpy.ops.mesh.edge_face_add()
        t.pd()
        t.up(d=0.001)
        t.up(d=wall_height - base_height - 0.011)
        t.up(d=0.01)
        t.select_all()

        bpy.ops.mesh.normals_make_consistent()

        bpy.ops.mesh.quads_convert_to_tris(
            quad_method='BEAUTY',
            ngon_method='BEAUTY')

        t.pu()
        t.deselect_all()
        t.home()
    
        core = bpy.context.object
        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        # create vert groups
        corner_wall_to_vert_groups(core, vert_locs)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        mode('OBJECT')
        bpy.ops.uv.smart_project(ctx, island_margin=0.05)

        return core

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
        booleans_path = os.path.join(preferences.assets_path, "meshes", "booleans", "openlock.blend")

        # load base cutters
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip', 'openlock.wall.base.cutter.clip.cap.start', 'openlock.wall.base.cutter.clip.cap.end']

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

        draw_corner_outline(
            cutter_triangles_2,
            angle,
            slot_width
        )

        # fill face and extrude cutter
        t = bpy.ops.turtle
        bpy.ops.mesh.edge_face_add()
        t.pd()
        t.up(d=slot_height)
        t.select_all()
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        t.pu()
        t.deselect_all()
        t.home()

        mode('OBJECT')
        cutter = bpy.context.object
        cutter.name = tile_props.tile_name + '.base.cutter'

        return cutter


class MT_L_Wall(MT_L_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_L_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_L_Tile.create_openlock_base(self, tile_props)
        return base

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['X Pos', 'Y Pos', 'X Neg', 'Y Neg']
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

        textured_vertex_groups = ['X Pos', 'Y Pos', 'X Neg', 'Y Neg']

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
                cutter.location[0] + 0.25,
                cutter.location[1] + tile_props.leg_2_len - 0.25,
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

        return preview_core

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


def calculate_corner_wall_triangles(
        leg_1_len,
        leg_2_len,
        thickness,
        angle):
    # X leg
    # right triangle
    tri_a_angle = angle / 2
    tri_a_adj = leg_1_len
    tri_a_opp = tri_a_adj * tan(radians(tri_a_angle))

    # right triangle
    tri_b_angle = 180 - tri_a_angle - 90
    tri_b_opp = tri_a_opp - thickness
    tri_b_adj = tri_b_opp * tan(radians(tri_b_angle))

    # Y leg
    # right triangle
    tri_c_angle = angle / 2
    tri_c_adj = leg_2_len
    tri_c_opp = tri_c_adj * tan(radians(tri_c_angle))

    tri_d_angle = 180 - tri_c_angle - 90
    tri_d_opp = tri_c_opp - thickness
    tri_d_adj = tri_d_opp * tan(radians(tri_d_angle))

    triangles = {
        'a_adj': tri_a_adj,  # leg 1 outer leg length
        'b_adj': tri_b_adj,  # leg 1 inner leg length
        'c_adj': tri_c_adj,  # leg 2 outer leg length
        'd_adj': tri_d_adj}  # leg 2 inner leg length

    return triangles


def move_cursor_to_wall_start(triangles, angle, thickness, base_height):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle
    t.add_turtle()
    orig_rot = turtle.rotation_euler.copy()
    t.pu()
    t.up(d=base_height, m=True)
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'])
    t.lt(d=90)
    t.fd(d=thickness)
    t.lt(d=90)
    t.fd(d=triangles['b_adj'])
    turtle.rotation_euler = orig_rot


def draw_corner_outline(triangles, angle, thickness):
    turtle = bpy.context.scene.cursor
    t = bpy.ops.turtle

    orig_loc = turtle.location.copy()
    orig_rot = turtle.rotation_euler.copy()

    # We save the location of each vertex as it is drawn
    # to use for making vert groups & positioning cutters
    vert_loc = {
        'origin': orig_loc
    }
    t.pd()
    # draw X leg
    t.rt(d=angle)
    t.fd(d=triangles['a_adj'] - 0.001)
    vert_loc['x_outer_1'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['x_outer_2'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=0.001)
    vert_loc['end_1_1'] = turtle.location.copy()
    t.fd(d=thickness - 0.002)
    vert_loc['end_1_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['end_1_3'] = turtle.location.copy()
    t.lt(d=90)
    t.fd(d=0.001)
    vert_loc['x_inner_1'] = turtle.location.copy()
    t.fd(d=triangles['b_adj'] - 0.001)
    vert_loc['x_inner_2'] = turtle.location.copy()
    # home
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    t.deselect_all()
    t.select_at_cursor(buffer=0.0001)
    t.pd()  # vert loc same as a

    # draw Y leg
    t.fd(d=triangles['c_adj'] - 0.001)
    vert_loc['y_outer_1'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['y_outer_2'] = turtle.location.copy()
    t.rt(d=90)

    t.fd(d=0.001)
    vert_loc['end_2_1'] = turtle.location.copy()

    t.fd(d=thickness - 0.002)
    vert_loc['end_2_2'] = turtle.location.copy()
    t.fd(d=0.001)
    vert_loc['end_2_3'] = turtle.location.copy()
    t.rt(d=90)
    t.fd(d=0.001)
    vert_loc['y_inner_1'] = turtle.location.copy()
    t.fd(d=triangles['d_adj'] - 0.001)  # vert loc same as x_inner_2

    t.select_all()
    t.merge()
    t.pu()
    turtle.location = orig_loc
    turtle.rotation_euler = orig_rot

    return vert_loc
