import bpy
from .. utils.registration import get_prefs
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.selection import select, deselect_all, activate
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials,
    add_preview_mesh_subsurf)
from .create_tile import MT_Tile
from ..lib.bmturtle.bmturtle import *


class MT_Connecting_Column_Tile(MT_Tile):
    def __init__(self, tile_props):
        self.tile_props = tile_props
        scene = bpy.context.scene
        cursor = scene.cursor
        cursor_orig_loc = cursor.location.copy()
        cursor_orig_rot = cursor.rotation_euler.copy()

        cursor.location = (0, 0, 0)
        cursor.rotation_euler = (0, 0, 0)

        base_blueprint = tile_props.base_blueprint
        main_part_blueprint = tile_props.main_part_blueprint

        if base_blueprint == 'PLAIN':
            base = self.create_plain_base(tile_props)

        ''' Openlock connecting columns don't have seperate base
        if base_blueprint == 'OPENLOCK':
            base = self.create_openlock_base(tile_props)
        '''

        if base_blueprint == 'NONE':
            base = self.create_empty_base(tile_props)

        if main_part_blueprint == 'PLAIN':
            preview_core = self.create_plain_cores(base, tile_props)

        if main_part_blueprint == 'OPENLOCK':
            base = self.create_empty_base(tile_props)
            preview_core = self.create_openlock_cores(base, tile_props)

        if main_part_blueprint == 'NONE':
            preview_core = None

        self.finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

    def create_plain_base(self, tile_props):
        base_size = tile_props.base_size
        tile_name = tile_props.tile_name

        # make base
        base = draw_cuboid(base_size) # TODO: Replace with bmturtle script
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

    def create_plain_cores(self, base, tile_props):
        textured_vertex_groups = ['Top', 'Sides']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core

    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size = (
            0.4,
            0.4,
            tile_props.tile_size[2])

        textured_vertex_groups = ['Top', 'Sides']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)

        displacement_core.hide_viewport = True
        return preview_core

    def create_core(self, tile_props):
        tile_name = tile_props.tile_name

        core = self.draw_core(tile_props)

        core.name = tile_name + '.core'
        add_object_to_collection(core, tile_name)

        ctx = {
            'object': core,
            'active_object': core,
            'selected_objects': [core],
            'selectable_objects': [core],
            'selected_editable_objects': [core]
        }

        bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)

        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name

        return core

    def draw_core(self, tile_props):
        native_subdivisions = (
            tile_props.x_native_subdivisions,
            tile_props.y_native_subdivisions,
            tile_props.z_native_subdivisions
        )
        tile_size = tile_props.tile_size
        base_size = tile_props.base_size
        col_size = (
            tile_size[0],
            tile_size[1],
            tile_size[2] - base_size[2])

        bm, obj = create_turtle('Column', ['Top', 'Bottom', 'Sides'])

        bm.verts.layers.deform.verify()
        deform_layer = bm.verts.layers.deform.active

        bm.select_mode = {'VERT'}

        bottom_verts = []
        side_verts = []

        # draw bottom
        subdiv_dist = col_size[1] / native_subdivisions[1]
        for i in range(native_subdivisions[1]):
            fd(bm, subdiv_dist)
        bm.select_mode = {'EDGE'}
        bm_select_all(bm)

        subdiv_dist = col_size[0] / native_subdivisions[0]
        for i in range(native_subdivisions[0]):
            ri(bm, subdiv_dist)

        # store verts to add to bottom vert group later.
        # If we add them now then verts created by extruding these verts will
        # also be added to vert group

        for v in bm.verts:
            bottom_verts.append(v)

        pu(bm)
        home(obj)
        pd(bm)

        # draw faces
        bm.select_mode = {'FACE'}
        bm_select_all(bm)

        # save index last vert we drew
        bm.verts.ensure_lookup_table()
        start_index = bm.verts[-1].index
        # draw ring so side verts don't project in wrong direction
        # because this is the first laye we don;t want to delete the original
        # geometry
        up(bm, 0.001, False)

        subdiv_dist = (col_size[2] - 0.002) / native_subdivisions[2]
        for i in range(native_subdivisions[2]):
            up(bm, subdiv_dist)

        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            if v.index > start_index and v.index <= bm.verts[-1].index:
                side_verts.append(v)

        up(bm, 0.001)

        # assign vertex groups
        for v in bm.verts:
            if v.select:
                groups = v[deform_layer]
                groups[0] = 1

        for v in bottom_verts:
            if v.is_valid:
                groups = v[deform_layer]
                groups[1] = 1

        for v in side_verts:
            if v.is_valid:
                groups = v[deform_layer]
                groups[2] = 1

        pu(bm)
        home(obj)

        finalise_turtle(bm, obj)

        return(obj)