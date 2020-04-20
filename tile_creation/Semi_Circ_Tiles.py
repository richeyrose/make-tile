import os
from math import radians
import bpy
from . create_tile import MT_Tile

from .. lib.turtle.scripts.curved_floor import (
    draw_neg_curved_slab,
    draw_pos_curved_slab,
    draw_openlock_pos_curved_base)
from .. lib.turtle.scripts.L_tile import (
    calculate_corner_wall_triangles,
    move_cursor_to_wall_start,
    draw_corner_3D)
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group
)
from .. utils.registration import get_prefs
from .. lib.utils.selection import select, deselect_all, select_by_loc, select_inverse_by_loc
from .. lib.utils.utils import mode
from .. lib.utils.collections import add_object_to_collection


class MT_Semi_Circ_Tile:
    def create_plain_base(self, tile_props):
        radius = tile_props.base_radius
        segments = tile_props.curve_native_subdivisions
        angle = tile_props.angle
        height = tile_props.base_size[2]
        curve_type = tile_props.curve_type
        native_subdivisions = (
            tile_props.x_native_subdivisions,
            tile_props.y_native_subdivisions,
            tile_props.z_native_subdivisions,
            tile_props.curve_native_subdivisions
        )


        if curve_type == 'POS':
            base = draw_pos_curved_slab(radius, segments, angle, height, native_subdivisions)
        else:
            base = draw_neg_curved_slab(radius, segments, angle, height, native_subdivisions)

        ctx = {
            'selected_objects': [base],
            'active_object': base
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        base.name = tile_props.tile_name + '.base'
        props = base.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name
        props.geometry_type = 'BASE'

        return base

    def create_openlock_base(self, tile_props):
        tile_props.base_size[2] = 0.2756

        length = tile_props.base_radius
        segments = tile_props.curve_native_subdivisions
        angle = tile_props.angle
        height = tile_props.base_size[2]
        curve_type = tile_props.curve_type
        native_subdivisions = (
            tile_props.x_native_subdivisions,
            tile_props.y_native_subdivisions,
            tile_props.z_native_subdivisions,
            tile_props.curve_native_subdivisions
        )

        if curve_type == 'POS':
            base = draw_openlock_pos_curved_base(length, segments, angle, height)
            base.mt_object_props.geometry_type = 'BASE'
            ctx = {
                'selected_objects': [base],
                'active_object': base
            }
            bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        else:
            draw_neg_curved_slab(length, segments, angle, height, native_subdivisions)
            base = bpy.context.object
            base.mt_object_props.geometry_type = 'BASE'
            ctx = {
                'selected_objects': [base],
                'active_object': base
            }
            bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

            if length >= 3:
                slot_cutter = self.create_openlock_neg_curve_base_cutters(tile_props)
                slot_cutter.parent = base
                slot_cutter.display_type = 'BOUNDS'
                slot_cutter.hide_viewport = True
                cutter_bool = base.modifiers.new('Slot Cutter', 'BOOLEAN')
                cutter_bool.operation = 'DIFFERENCE'
                cutter_bool.object = slot_cutter

        cutters = self.create_openlock_base_clip_cutters(tile_props)

        for clip_cutter in cutters:
            matrixcopy = clip_cutter.matrix_world.copy()
            clip_cutter.parent = base
            clip_cutter.matrix_world = matrixcopy
            clip_cutter.display_type = 'BOUNDS'
            clip_cutter.hide_viewport = True
            clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
            clip_cutter_bool.operation = 'DIFFERENCE'
            clip_cutter_bool.object = clip_cutter

        base.name = tile_props.tile_name + '.base'
        props = base.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name
        props.geometry_type = 'BASE'

        return base

    def create_openlock_neg_curve_base_cutters(self, tile_props):
        length = tile_props.base_radius / 2
        angle = tile_props.angle
        face_dist = 0.233
        slot_width = 0.197
        slot_height = 0.25
        end_dist = 0.236  # distance of slot from base end

        cutter_triangles_1 = calculate_corner_wall_triangles(
            length,
            length,
            face_dist,
            angle)

        # reuse method we use to work out where to start our corner wall
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
            slot_height
        )

        cutter.name = tile_props.tile_name + '.base.cutter'

        props = cutter.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name
        props.geometry_type = 'CUTTER'
        return cutter

    def create_openlock_base_clip_cutters(self, tile_props):
        mode('OBJECT')

        cursor = bpy.context.scene.cursor
        cursor_orig_loc = cursor.location.copy()

        radius = tile_props.base_radius
        angle = tile_props.angle
        curve_type = tile_props.curve_type
        cutters = []
        if curve_type == 'NEG':
            radius = radius / 2

        if radius >= 1:
            preferences = get_prefs()
            booleans_path = os.path.join(
                preferences.assets_path,
                "meshes", "booleans", "openlock.blend")

            with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
                data_to.objects = ['openlock.wall.base.cutter.clip',
                                   'openlock.wall.base.cutter.clip.cap.start',
                                   'openlock.wall.base.cutter.clip.cap.end']

            for obj in data_to.objects:
                add_object_to_collection(obj, tile_props.tile_name)

            clip_cutter_1 = data_to.objects[0]
            cutter_start_cap = data_to.objects[1]
            cutter_end_cap = data_to.objects[2]

            cutter_start_cap.hide_viewport = True
            cutter_end_cap.hide_viewport = True

            array_mod = clip_cutter_1.modifiers.new('Array', 'ARRAY')
            array_mod.start_cap = cutter_start_cap
            array_mod.end_cap = cutter_end_cap
            array_mod.use_merge_vertices = True

            array_mod.fit_type = 'FIT_LENGTH'

            if angle >= 90:
                clip_cutter_1.location = (
                    cursor_orig_loc[0] + 0.5,
                    cursor_orig_loc[1] + 0.25,
                    cursor_orig_loc[2]
                )
                array_mod.fit_length = radius - 1
            else:
                clip_cutter_1.location = (
                    cursor_orig_loc[0] + 1,
                    cursor_orig_loc[1] + 0.25,
                    cursor_orig_loc[2]
                )
                array_mod.fit_length = radius - 1.5

            deselect_all()
            select(clip_cutter_1.name)

            bpy.ops.transform.rotate(
                value=(radians(angle - 90)),
                orient_axis='Z',
                orient_type='GLOBAL',
                center_override=cursor_orig_loc)

            cutters.append(clip_cutter_1)
            # cutter 2
            clip_cutter_2 = clip_cutter_1.copy()
            add_object_to_collection(clip_cutter_2, tile_props.tile_name)

            array_mod = clip_cutter_2.modifiers['Array']

            if angle >= 90:
                clip_cutter_2.location = (
                    cursor_orig_loc[0] + 0.25,
                    cursor_orig_loc[1] + radius - 0.5,
                    cursor_orig_loc[2]
                )
                array_mod.fit_length = radius - 1
            else:
                clip_cutter_2.location = (
                    cursor_orig_loc[0] + 0.25,
                    cursor_orig_loc[1] + radius - 0.5,
                    cursor_orig_loc[2]
                )
                array_mod.fit_length = radius - 1.5

            clip_cutter_2.rotation_euler = (0, 0, radians(-90))
            cutters.append(clip_cutter_2)

            deselect_all()

        if tile_props.curve_type == 'POS':
            with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
                data_to.objects = ['openlock.wall.base.cutter.clip_single']
            clip_cutter_3 = data_to.objects[0]
            add_object_to_collection(clip_cutter_3, tile_props.tile_name)

            deselect_all()
            select(clip_cutter_3.name)

            clip_cutter_3.rotation_euler = (0, 0, radians(180))
            clip_cutter_3.location[1] = cursor_orig_loc[1] + radius - 0.25
            bpy.ops.transform.rotate(
                value=(radians(angle / 2)),
                orient_axis='Z',
                orient_type='GLOBAL',
                center_override=cursor_orig_loc)

            cutters.append(clip_cutter_3)

        for cutter in cutters:
            props = cutter.mt_object_props
            props.is_mt_object = True
            props.tile_name = tile_props.tile_name
            props.geometry_type = 'CUTTER'

        return cutters


class MT_Semi_Circ_Floor_Tile(MT_Semi_Circ_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

        if tile_props.tile_blueprint == 'OPENLOCK' or \
                tile_props.base_blueprint == 'OPENLOCK':

            tile_props.base_size = (
                tile_props.tile_size[0],
                tile_props.tile_size[1],
                0.2755)

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['Top']

        core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return core

    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size = (
            tile_props.tile_size[0],
            tile_props.tile_size[1],
            0.3)

        core = self.create_plain_cores(base, tile_props)
        return core

    def create_core(self, tile_props):
        '''Returns the core (top) part of a floor tile
        '''
        base_size = tile_props.base_size
        radius = tile_props.base_radius
        segments = tile_props.curve_native_subdivisions
        angle = tile_props.angle
        height = tile_props.tile_size[2] - base_size[2]
        curve_type = tile_props.curve_type
        native_subdivisions = (
            tile_props.x_native_subdivisions,
            tile_props.y_native_subdivisions,
            tile_props.z_native_subdivisions,
            tile_props.curve_native_subdivisions
        )

        if curve_type == 'POS':
            core = draw_pos_curved_slab(
                radius,
                segments,
                angle,
                height,
                native_subdivisions)
            curved_floor_to_vert_groups(
                core,
                height,
                radius)
        else:
            core, vert_locs = draw_neg_curved_slab(
                radius,
                segments,
                angle,
                height,
                native_subdivisions,
                return_vert_locs=True)
            neg_curved_floor_to_vert_groups(
                core,
                height,
                radius,
                vert_locs
            )

        core.location[2] = core.location[2] + base_size[2]
        core.name = tile_props.tile_name + '.core'

        ctx = {
            'selected_editable_objects': [core],
            'selected_objects': [core],
            'object': core,
            'active_object': core
        }

        bpy.ops.uv.smart_project(ctx, island_margin=0.05)
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        return core


def neg_curved_floor_to_vert_groups(obj, height, side_length, vert_locs):
    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj]
    }

    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')
    select(obj.name)
    mode('EDIT')
    deselect_all()

    select_by_loc(
        lbound=(obj.location),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2]),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    for key, value in vert_locs.items():
        if key == 'side_a':
            for v in value:
                select_by_loc(
                    lbound=v,
                    ubound=(v[0], v[1], v[2] + height),
                    select_mode='VERT',
                    coords='GLOBAL',
                    additive=True,
                    buffer=0.0001
                )

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        additive=True,
        coords='GLOBAL'
    )

    bpy.ops.object.vertex_group_set_active(ctx, group='Side a')
    bpy.ops.object.vertex_group_assign(ctx)
    deselect_all()

    # side b
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )

    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    mode('OBJECT')

    # get verts in side groups
    side_groups = ['Side a', 'Side b', 'Side c']
    side_vert_indices = []

    for group in side_groups:
        verts = get_vert_indexes_in_vert_group(group, bpy.context.object)
        side_vert_indices.extend(verts)

    remove_verts_from_group('Top', bpy.context.object, side_vert_indices)


def curved_floor_to_vert_groups(obj, height, side_length):
    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Top')
    select(obj.name)
    mode('EDIT')

    deselect_all()
    select_by_loc(
        lbound=(obj.location),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2]),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0] + side_length,
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1] + side_length,
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side b')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    select_inverse_by_loc(
        lbound=(
            obj.location[0],
            obj.location[1],
            obj.location[2]),
        ubound=(
            obj.location[0],
            obj.location[1],
            obj.location[2] + height),
        buffer=0.0001,
        coords='GLOBAL'
    )
    bpy.ops.object.vertex_group_set_active(group='Side a')
    bpy.ops.object.vertex_group_assign()

    mode('OBJECT')
