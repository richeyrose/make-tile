import os
from math import radians
import bpy
from . create_tile import MT_Tile
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.triangular_tile import (
    draw_plain_triangular_base,
    draw_tri_floor_core,
    draw_openlock_tri_floor_base)
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.utils import mode
from .. lib.utils.selection import select, deselect_all, select_by_loc
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group)


class MT_Triangular_Floor_Tile(MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        tile_name = tile_props.tile_name
        base, dimensions = draw_plain_triangular_base(tile_props)
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
        tile_props.base_size[2] = .2756
        tile_props.tile_size[2] = 0.3
        tile_name = tile_props.tile_name

        base, dimensions = draw_openlock_tri_floor_base(
            tile_props.leg_1_len,
            tile_props.leg_2_len,
            tile_props.base_size[2],
            tile_props.angle)

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

        clip_cutters = self.create_openlock_base_clip_cutters(dimensions, tile_props)

        for clip_cutter in clip_cutters:
            matrixcopy = clip_cutter.matrix_world.copy()
            clip_cutter.parent = base
            clip_cutter.matrix_world = matrixcopy
            clip_cutter.display_type = 'BOUNDS'
            clip_cutter.hide_viewport = True
            clip_cutter_bool = base.modifiers.new('Clip Cutter', 'BOOLEAN')
            clip_cutter_bool.operation = 'DIFFERENCE'
            clip_cutter_bool.object = clip_cutter
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
        tile_props.tile_size[2] = 0.3
        preview_core = self.create_plain_cores(base, tile_props)
        return preview_core

    def create_core(self, tile_props):
        tile_name = tile_props.tile_name
        native_subdivisions = (
            tile_props.opposite_native_subdivisions,
            tile_props.z_native_subdivisions)

        core, dimensions = draw_tri_floor_core(
            tile_props.leg_1_len,
            tile_props.leg_2_len,
            tile_props.angle,
            tile_props.tile_size[2] - tile_props.base_size[2],
            native_subdivisions)

        core.name = tile_name + '.core'
        add_object_to_collection(core, tile_name)

        tri_floor_to_vert_groups(
            core,
            dimensions,
            tile_props.tile_size[2] - tile_props.base_size[2],
            tile_props.base_size[2],
            native_subdivisions)

        mode('OBJECT')

        core.location[2] = core.location[2] + tile_props.base_size[2]

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=0.012)
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core

    def create_openlock_base_clip_cutters(self, dimensions, tile_props):
        if dimensions['a'] or dimensions['b'] or dimensions['c'] >= 2:
            mode('OBJECT')
            deselect_all()
            preferences = get_prefs()
            booleans_path = os.path.join(
                preferences.assets_path,
                "meshes",
                "booleans",
                "openlock.blend")

            cutters = []
            with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
                data_to.objects = [
                    'openlock.wall.base.cutter.clip',
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

            # for cutters the number of cutters and start and end location has to take into account
            # the angles of the triangle in order to prevent overlaps between cutters
            # and issues with booleans

            # cutter 1
            if dimensions['c'] >= 2:
                if dimensions['A'] >= 90:
                    clip_cutter_1.location = (
                        dimensions['loc_A'][0] + 0.5,
                        dimensions['loc_A'][1] + 0.25,
                        dimensions['loc_A'][2])
                    if dimensions['C'] >= 90:
                        array_mod.fit_length = dimensions['c'] - 1
                    else:
                        array_mod.fit_length = dimensions['c'] - 1.5

                elif dimensions['A'] < 90:
                    clip_cutter_1.location = (
                        dimensions['loc_A'][0] + 1,
                        dimensions['loc_A'][1] + 0.25,
                        dimensions['loc_A'][2])
                    if dimensions['C'] >= 90:
                        array_mod.fit_length = dimensions['c'] - 1.5
                    else:
                        array_mod.fit_length = dimensions['c'] - 2

                deselect_all()
                select(clip_cutter_1.name)
                bpy.ops.transform.rotate(
                    value=(radians(dimensions['A'] - 90)),
                    orient_axis='Z',
                    orient_type='GLOBAL',
                    center_override=dimensions['loc_A'])

                deselect_all()

                # cutter 2
                clip_cutter_2 = clip_cutter_1.copy()
                add_object_to_collection(clip_cutter_2, tile_props.tile_name)
                cutters.append(clip_cutter_1)
            else:
                clip_cutter_2 = clip_cutter_1

            if dimensions['b'] >= 2:
                array_mod = clip_cutter_2.modifiers['Array']

                if dimensions['B'] >= 90:
                    clip_cutter_2.location = (
                        dimensions['loc_B'][0] + 0.25,
                        dimensions['loc_B'][1] - 0.5,
                        dimensions['loc_B'][2])
                    if dimensions['A'] >= 90:
                        array_mod.fit_length = dimensions['b'] - 1
                    else:
                        array_mod.fit_length = dimensions['b'] - 1.5

                elif dimensions['B'] < 90:
                    clip_cutter_2.location = (
                        dimensions['loc_B'][0] + 0.25,
                        dimensions['loc_B'][1] - 1,
                        dimensions['loc_B'][2])
                    if dimensions['A'] >= 90:
                        array_mod.fit_length = dimensions['b'] - 1.5
                    else:
                        array_mod.fit_length = dimensions['b'] - 2

                clip_cutter_2.rotation_euler = (0, 0, radians(-90))
                cutters.append(clip_cutter_2)
                if dimensions['a'] >= 2:
                    clip_cutter_3 = clip_cutter_2.copy()
                    add_object_to_collection(clip_cutter_3, tile_props.tile_name)
                else:
                    bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)
                    return cutters
            else:
                clip_cutter_3 = clip_cutter_2

            # clip cutter 3
            if dimensions['a'] >= 2:
                clip_cutter_3.rotation_euler = (0, 0, 0)
                array_mod = clip_cutter_3.modifiers['Array']

                if dimensions['C'] >= 90:
                    clip_cutter_3.location = (
                        dimensions['loc_C'][0] + 0.5,
                        dimensions['loc_C'][1] + 0.25,
                        dimensions['loc_C'][2])
                    if dimensions['B'] >= 90:
                        array_mod.fit_length = dimensions['a'] - 1
                    else:
                        array_mod.fit_length = dimensions['a'] - 1.5

                elif dimensions['C'] < 90:
                    clip_cutter_3.location = (
                        dimensions['loc_C'][0] + 1,
                        dimensions['loc_C'][1] + 0.25,
                        dimensions['loc_C'][2])
                    if dimensions['B'] >= 90:
                        array_mod.fit_length = dimensions['a'] - 1.5
                    else:
                        array_mod.fit_length = dimensions['a'] - 2
                deselect_all()
                select(clip_cutter_3.name)

                bpy.ops.transform.rotate(
                    value=(-radians(90 + dimensions['C'])),
                    orient_axis='Z',
                    orient_type='GLOBAL',
                    center_override=dimensions['loc_C'])

                deselect_all()
                cutters.append(clip_cutter_3)
                bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

            return cutters
        else:
            return None


def tri_floor_to_vert_groups(obj, dim, height, base_height, native_subdivisions):
    # make vertex groups
    obj.vertex_groups.new(name='Top')
    obj.vertex_groups.new(name='Bottom')
    obj.vertex_groups.new(name='Side a')
    obj.vertex_groups.new(name='Side b')
    obj.vertex_groups.new(name='Side c')

    mode('EDIT')

    deselect_all()
    select_by_loc(
        lbound=(
            dim['loc_A'][0],
            dim['loc_A'][1],
            dim['loc_A'][2] + height),
        ubound=(
            dim['loc_B'][0] + dim['a'],
            dim['loc_B'][1],
            dim['loc_B'][2] + height),
        buffer=0.0001,
        select_mode='FACE'
    )

    bpy.ops.object.vertex_group_set_active(group='Top')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    select_by_loc(
        lbound=(
            dim['loc_A'][0],
            dim['loc_A'][1],
            dim['loc_A'][2]),
        ubound=(
            dim['loc_B'][0] + dim['a'],
            dim['loc_B'][1],
            dim['loc_B'][2]),
    )
    bpy.ops.object.vertex_group_set_active(group='Bottom')
    bpy.ops.object.vertex_group_assign()
    deselect_all()

    subdivided_height = height / native_subdivisions[1]
    bpy.ops.object.vertex_group_set_active(group='Side a')
    i = 0
    while i <= native_subdivisions[1]:
        select_by_loc(
            lbound=(
                dim['loc_C'][0],
                dim['loc_C'][1],
                dim['loc_C'][2] + (subdivided_height * i)),
            ubound=(
                dim['loc_C'][0],
                dim['loc_C'][1],
                dim['loc_C'][2] + (subdivided_height * i)),
            buffer=0.0001,
            additive=True
        )

        select_by_loc(
            lbound=(
                dim['loc_B'][0],
                dim['loc_B'][1],
                dim['loc_B'][2] + (subdivided_height * i)),
            ubound=(
                dim['loc_B'][0],
                dim['loc_B'][1],
                dim['loc_B'][2] + (subdivided_height * i)),
            buffer=0.0001,
            additive=True
        )
        bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign()
        deselect_all()
        i += 1

    bpy.ops.object.vertex_group_set_active(group='Side b')

    i = 0
    while i <= native_subdivisions[1]:
        select_by_loc(
            lbound=(
                dim['loc_A'][0],
                dim['loc_A'][1],
                dim['loc_A'][2] + (subdivided_height * i)),
            ubound=(
                dim['loc_A'][0],
                dim['loc_A'][1],
                dim['loc_A'][2] + (subdivided_height * i)),
            additive=True,
            buffer=0.0001
        )

        select_by_loc(
            lbound=(
                dim['loc_C'][0],
                dim['loc_C'][1],
                dim['loc_C'][2] + (subdivided_height * i)),
            ubound=(
                dim['loc_C'][0],
                dim['loc_C'][1],
                dim['loc_C'][2] + (subdivided_height * i)),
            buffer=0.0001,
            additive=True
        )
        bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
        bpy.ops.object.vertex_group_assign()
        deselect_all()
        i += 1

    select_by_loc(
        lbound=dim['loc_A'],
        ubound=(
            dim['loc_B'][0],
            dim['loc_B'][1],
            dim['loc_B'][2] + base_height),
        buffer=0.0001
    )
    bpy.ops.object.vertex_group_set_active(group='Side c')
    bpy.ops.object.vertex_group_assign()

    deselect_all()
    mode('OBJECT')

    side_verts = []
    sides = ['Side a', 'Side b', 'Side c']

    for side in sides:
        verts = get_vert_indexes_in_vert_group(side, bpy.context.object)
        side_verts.extend(verts)

    remove_verts_from_group('Top', bpy.context.object, side_verts)
