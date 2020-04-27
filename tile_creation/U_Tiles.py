import os
import bpy
import bmesh
from mathutils import Vector
from .. lib.utils.utils import mode, vectors_are_close
from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    deselect_all,
    select)
from . create_tile import MT_Tile
from .. lib.utils.collections import add_object_to_collection

#MIXIN
class MT_U_Tile:
    def create_plain_base(self, tile_props):
        '''
        leg_1_len and leg_2_len are the inner lengths of the legs
                    ||           ||
                    ||leg_1 leg_2||
                    ||           ||
                    ||___inner___||
             origin x--------------
                        outer
        '''
        leg_1_inner_len = tile_props.leg_1_len
        leg_2_inner_len = tile_props.leg_2_len
        thickness = tile_props.base_size[1]
        z_height = tile_props.base_size[2]
        x_inner_len = tile_props.tile_size[0]

        base = self.draw_plain_base(leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height)

        base.name = tile_props.tile_name + '.base'
        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base

    def create_openlock_base_slot_cutter(self, tile_props):
        leg_1_inner_len = tile_props.leg_1_len
        leg_2_inner_len = tile_props.leg_2_len
        thickness = tile_props.base_size[1]
        z_height = tile_props.base_size[2]
        x_inner_len = tile_props.tile_size[0]

        leg_1_outer_len = leg_1_inner_len + thickness
        leg_2_outer_len = leg_2_inner_len + thickness
        x_outer_len = x_inner_len + (thickness * 2)

        preferences = get_prefs()

        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes",
            "booleans",
            "openlock.blend")

        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'openlock.u_tile.base.cutter.slot.root',
                'openlock.u_tile.base.cutter.slot.start_cap.root',
                'openlock.u_tile.base.cutter.slot.end_cap.root']


        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)
            obj.hide_viewport = True

        slot_cutter = data_to.objects[0]
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        slot_cutter.hide_viewport = False

        return slot_cutter

    def create_openlock_base(self, tile_props):
        tile_props.base_size = Vector((1, 0.5, 0.2755))

        base = self.create_plain_base(tile_props)

        slot_cutter = self.create_openlock_base_slot_cutter(tile_props)
        return base

    def draw_plain_base(self, leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height):
        '''
                    ||           ||
                    ||leg_1 leg_2||
                    ||           ||
                    ||___inner___||
            origin x--------------
                        outer
        '''
        mode('OBJECT')

        leg_1_outer_len = leg_1_inner_len + thickness
        leg_2_outer_len = leg_2_inner_len + thickness
        x_outer_len = x_inner_len + (thickness * 2)

        t = bpy.ops.turtle
        t.add_turtle()

        t.fd(d=leg_1_outer_len)
        t.rt(d=90)
        t.fd(d=thickness)
        t.rt(d=90)
        t.fd(d=leg_1_inner_len)
        t.lt(d=90)
        t.fd(d=x_inner_len)
        t.lt(d=90)
        t.fd(d=leg_2_inner_len)
        t.rt(d=90)
        t.fd(d=thickness)
        t.rt(d=90)
        t.fd(d=leg_2_outer_len)
        t.rt(d=90)
        t.fd(d=x_outer_len)
        t.select_all()
        t.merge()
        bpy.ops.mesh.edge_face_add()
        t.up(d=z_height)
        t.select_all()
        bpy.ops.mesh.normals_make_consistent()
        mode('OBJECT')
        return bpy.context.object


class MT_U_Wall_Tile(MT_U_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        base = MT_U_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_U_Tile.create_openlock_base(self, tile_props)
        return base

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 1 Top', 'End Wall Inner', 'End Wall Outer', 'End Wall Top', 'Leg 2 Inner', 'Leg 2 Outer', 'Leg 2 Top']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size[1] = 0.3149
        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'Leg 1 Top', 'End Wall Inner', 'End Wall Outer', 'End Wall Top', 'Leg 2 Inner', 'Leg 2 Outer', 'Leg 2 Top']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_core(self, tile_props):
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        base_thickness = tile_props.base_size[1]
        core_thickness = tile_props.tile_size[1]
        base_height = tile_props.base_size[2]
        wall_height = tile_props.tile_size[2]
        x_inner_len = tile_props.tile_size[0]
        thickness_diff = base_thickness - core_thickness
        native_subdivisions = (
            tile_props.leg_1_native_subdivisions,
            tile_props.leg_2_native_subdivisions,
            tile_props.x_native_subdivisions,
            tile_props.width_native_subdivisions,
            tile_props.z_native_subdivisions)

        core, vert_locs = self.draw_core(
            leg_1_len,
            leg_2_len,
            x_inner_len,
            core_thickness,
            wall_height - base_height,
            native_subdivisions,
            thickness_diff)

        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        self.create_vertex_groups(core, vert_locs, native_subdivisions)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core]
        }

        mode('OBJECT')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
        bpy.context.scene.cursor.location = (0, 0, 0)
        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        return core


    def draw_core(self, leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height, native_subdivisions, thickness_diff):
        '''
                    ||           ||
                    ||leg_1 leg_2||
                    ||           ||
                    ||___inner___||
            origin x--------------
                        outer
        '''

        mode('OBJECT')

        leg_1_inner_len = leg_1_inner_len + (thickness_diff / 2)
        leg_2_inner_len = leg_2_inner_len + (thickness_diff / 2)
        x_inner_len = x_inner_len + thickness_diff

        leg_1_outer_len = leg_1_inner_len + thickness
        leg_2_outer_len = leg_2_inner_len + thickness

        x_outer_len = x_inner_len + (thickness * 2)

        t = bpy.ops.turtle
        t.add_turtle()

        obj = bpy.context.object
        ctx = {
            'object': obj,
            'active_object': obj,
            'selected_objects':[obj]
            }
        # We save the location of each vertex as it is drawn
        # to use for making vert groups & positioning cutters
        verts = bpy.context.object.data.vertices

        leg_1_outer_verts = []
        leg_1_inner_verts = []
        leg_1_end_verts = []

        x_outer_verts = []
        x_inner_verts = []

        leg_2_outer_verts = []
        leg_2_inner_verts = []
        leg_2_end_verts = []

        bottom_verts = []
        inset_verts = []

        # move cursor to start location
        t.pu()
        t.fd(d=thickness_diff / 2)
        t.ri(d=thickness_diff / 2)
        t.pd()

        # draw leg 1 outer
        subdiv_dist = (leg_1_outer_len - 0.001) / native_subdivisions[0]

        for v in range(native_subdivisions[0]):
            t.fd(d=subdiv_dist)
        t.fd(d=0.001)

        for v in verts:
            leg_1_outer_verts.append(v.co.copy())

        # draw leg 1 end
        t.rt(d=90)
        t.pu()
        leg_1_end_verts.append(verts[verts.values()[-1].index].co.copy())
        t.fd(d=thickness)
        t.pd()
        t.add_vert()
        leg_1_end_verts.append(verts[verts.values()[-1].index].co.copy())

        # draw leg 1 inner
        subdiv_dist = (leg_1_inner_len - 0.001) / native_subdivisions[0]
        t.rt(d=90)
        t.fd(d=0.001)

        start_index = verts.values()[-1].index
        for v in range(native_subdivisions[0]):
            t.fd(d=subdiv_dist)

        i = start_index + 1
        while i <= verts.values()[-1].index:
            leg_1_inner_verts.append(verts[i].co.copy())
            i += 1
        t.deselect_all()
        leg_1_inner_verts.append(verts[verts.values()[-1].index].co.copy())

        # draw x inner
        subdiv_dist = x_inner_len / native_subdivisions[2]
        t.lt(d=90)

        t.add_vert()
        start_index = verts.values()[-1].index
        for v in range(native_subdivisions[2]):
            t.fd(d=subdiv_dist)

        i = start_index
        while i <= verts.values()[-1].index:
            x_inner_verts.append(verts[i].co.copy())
            i += 1
        t.deselect_all()
        x_inner_verts.append(verts[verts.values()[-1].index].co.copy())

        # draw leg 2 inner
        subdiv_dist = (leg_2_inner_len - 0.001) / native_subdivisions[1]

        t.lt(d=90)
        t.add_vert()
        start_index = verts.values()[-1].index
        for v in range(native_subdivisions[1]):
            t.fd(d=subdiv_dist)
        t.fd(d=0.001)

        i = start_index
        while i <= verts.values()[-1].index:
            leg_2_inner_verts.append(verts[i].co.copy())
            i += 1
        t.deselect_all()

        # draw leg 2  end
        t.add_vert()
        leg_2_end_verts.append(verts[verts.values()[-1].index].co.copy())
        t.rt(d=90)
        t.pu()
        t.fd(d=thickness)
        t.pd()
        t.add_vert()
        leg_2_end_verts.append(verts[verts.values()[-1].index].co.copy())

        # draw leg 2 outer
        subdiv_dist = (leg_2_outer_len - 0.001) / native_subdivisions[1]
        t.rt(d=90)
        t.fd(d=0.001)

        start_index = verts.values()[-1].index

        for v in range(native_subdivisions[1]):
            t.fd(d=subdiv_dist)

        i = start_index + 1
        while i <= verts.values()[-1].index:
            leg_2_outer_verts.append(verts[i].co.copy())
            i += 1
        t.deselect_all()
        leg_2_outer_verts.append(verts[verts.values()[-1].index].co.copy())

        # draw x outer
        subdiv_dist = x_outer_len / native_subdivisions[2]
        t.add_vert()
        t.rt(d=90)

        start_index = verts.values()[-1].index
        for v in range(native_subdivisions[2]):
            t.fd(d=subdiv_dist)

        i = start_index
        while i <= verts.values()[-1].index:
            x_outer_verts.append(verts[i].co.copy())
            i += 1

        t.deselect_all()
        x_outer_verts.append(verts[i].co.copy())
        t.select_all()
        t.merge()
        t.pu()
        t.home()
        bpy.ops.mesh.bridge_edge_loops(ctx, type='CLOSED', twist_offset=0, number_cuts=native_subdivisions[3], interpolation='LINEAR')
        bpy.ops.mesh.inset(ctx, use_boundary=True, use_even_offset=True, thickness=0.001, depth=0)

        t.select_all()
        t.merge()

        # extrude vertically
        t.pd()
        subdiv_dist = (z_height - 0.002) / native_subdivisions[4]
        t.up(d=0.001)
        for v in range(native_subdivisions[4]):
            t.up(d=subdiv_dist)
        t.up(d=0.001)
        t.select_all()
        bpy.ops.mesh.normals_make_consistent(ctx)
        t.deselect_all()

        mode('OBJECT')

        vert_locs = {
            'Leg 1 Outer': leg_1_outer_verts,
            'Leg 1 Inner': leg_1_inner_verts,
            'Leg 1 End': leg_1_end_verts,
            'Leg 2 Outer': leg_2_outer_verts,
            'Leg 2 Inner': leg_2_inner_verts,
            'Leg 2 End': leg_2_end_verts,
            'End Wall Inner': x_inner_verts,
            'End Wall Outer': x_outer_verts
        }

        return obj, vert_locs

    def create_vertex_groups(self, obj, vert_locs, native_subdivisions):
        ctx = {
            'object': obj,
            'active_object': obj,
            'selected_objects': [obj]
        }
        select(obj.name)
        mode('EDIT')
        deselect_all()

        # make vertex groups
        obj.vertex_groups.new(name='Leg 1 Inner')
        obj.vertex_groups.new(name='Leg 1 Outer')
        obj.vertex_groups.new(name='Leg 1 End')
        obj.vertex_groups.new(name='Leg 1 Top')
        obj.vertex_groups.new(name='Leg 1 Bottom')

        obj.vertex_groups.new(name='Leg 2 Inner')
        obj.vertex_groups.new(name='Leg 2 Outer')
        obj.vertex_groups.new(name='Leg 2 End')
        obj.vertex_groups.new(name='Leg 2 Top')
        obj.vertex_groups.new(name='Leg 2 Bottom')

        obj.vertex_groups.new(name='End Wall Inner')
        obj.vertex_groups.new(name='End Wall Outer')
        obj.vertex_groups.new(name='End Wall Top')
        obj.vertex_groups.new(name='End Wall Bottom')

        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        bm.faces.ensure_lookup_table()

        # inner and outer faces
        groups = ('Leg 1 Inner', 'Leg 1 Outer', 'Leg 2 Inner', 'Leg 2 Outer', 'End Wall Inner', 'End Wall Outer')

        for vert_group in groups:
            for v in bm.verts:
                v.select = False

            bpy.ops.object.vertex_group_set_active(ctx, group=vert_group)
            vert_coords = vert_locs[vert_group].copy()
            subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[4]

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
            while i <= native_subdivisions[4]:
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
            subdiv_dist = (obj.dimensions[2] - 0.002) / native_subdivisions[4]

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
            while i < native_subdivisions[4]:
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


        # leg 1 bottom

        bpy.ops.object.vertex_group_set_active(ctx, group='Leg 1 Bottom')
        inner_vert_locs = vert_locs['Leg 1 Inner'][::-1]
        outer_vert_locs = vert_locs['Leg 1 Outer']

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

        # Leg 2 bottom
        bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Bottom')
        inner_vert_locs = vert_locs['Leg 2 Inner']
        outer_vert_locs = vert_locs['Leg 2 Outer'][::-1]

        for v in bm.verts:
            v.select = False

        i = 0
        while i < len(inner_vert_locs):
            for v in bm.verts:
                if (vectors_are_close(v.co, outer_vert_locs[i], 0.0001)):
                    v.select = True
                    break

            for v in bm.verts:
                if (vectors_are_close(v.co, inner_vert_locs[i], 0.0001)):
                    v.select = True
                    break

            bpy.ops.mesh.shortest_path_select(ctx, edge_mode='SELECT')
            bpy.ops.object.vertex_group_assign(ctx)

            for v in bm.verts:
                v.select = False

            i += 1

        # End Wall Bottom
        bpy.ops.object.vertex_group_set_active(ctx, group='End Wall Bottom')
        inner_vert_locs = vert_locs['End Wall Inner'][::-1]
        outer_vert_locs = vert_locs['End Wall Outer']

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

        # leg 2 top
        bpy.ops.object.vertex_group_set_active(ctx, group='Leg 2 Top')

        inner_vert_locs = vert_locs['Leg 2 Inner'].copy()
        outer_vert_locs = vert_locs['Leg 2 Outer'][::-1].copy()

        for index, coord in enumerate(inner_vert_locs):
            inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

        for index, coord in enumerate(outer_vert_locs):
            outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

        for v in bm.verts:
            v.select = False

        i = 0
        while i < len(inner_vert_locs):
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

        # End wall top
        bpy.ops.object.vertex_group_set_active(ctx, group='End Wall Top')

        inner_vert_locs = vert_locs['End Wall Inner'][::-1].copy()
        outer_vert_locs = vert_locs['End Wall Outer'].copy()

        for index, coord in enumerate(inner_vert_locs):
            inner_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

        for index, coord in enumerate(outer_vert_locs):
            outer_vert_locs[index] = Vector((0, 0, obj.dimensions[2])) + coord

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

        bmesh.update_edit_mesh(bpy.context.object.data)

        mode('OBJECT')
