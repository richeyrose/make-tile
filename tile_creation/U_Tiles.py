import os
from math import radians
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.vertex_groups import (
    corner_wall_to_vert_groups,
    corner_floor_to_vert_groups)
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    deselect_all,
    select)
from . create_tile import MT_Tile
from .. lib.turtle.scripts.U_tile import (
    draw_u_3D)
from .. lib.turtle.scripts.L_Tile import (
    calculate_corner_wall_triangles,
    move_cursor_to_wall_start)


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
        leg_1_len = tile_props.leg_1_len
        leg_2_len = tile_props.leg_2_len
        thickness = tile_props.base_size[1]
        height = tile_props.base_size[2]
        inner_len = tile_props.base_size[0]

        base, vert_locs = draw_u_3D(leg_1_len, leg_2_len, thickness, height, inner_len, True)

        base.name = tile_props.tile_name + '.base'
        obj_props = base.mt_object_props
        obj_props.is_mt_object = True
        obj_props.geometry_type = 'BASE'
        obj_props.tile_name = tile_props.tile_name

        return base, vert_locs
    
    def create_openlock_base(self, tile_props):
        tile_props.base_size = Vector((1, 0.5, 0.2755))
        
        base, vert_locs = self.create_plain_base(tile_props)

class MT_U_Wall(MT_U_Tile, MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)
        
    def create_plain_base(self, tile_props):
        base = MT_U_Tile.create_plain_base(self, tile_props)
        return base

    def create_openlock_base(self, tile_props):
        base = MT_U_Tile.create_openlock_base(self, tile_props)
        return base
    
    def create_plain_cores(self, base, tile_props):    
        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'End Wall Inner', 'End Wall Outer','Leg 2 Inner', 'Leg 2 Outer']
        preview_core, displacement_core = self.create_cores(
            base,
            tile_props,
            textured_vertex_groups)
        displacement_core.hide_viewport = True
        return preview_core
    
    def create_openlock_cores(self, base, tile_props):
        tile_props.tile_size[1] = 0.3149
        textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'End Wall Inner', 'End Wall Outer','Leg 2 Inner', 'Leg 2 Outer']
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
        wall_thickness = tile_props.base_size[1]
        base_height = tile_props.base_size[2]
        wall_height = tile_props.tile_size[2]
        inner_len = tile_props.tile_size[0]
        angle = 90
        thickness_diff = base_thickness - wall_thickness
        
        # first work out where we're going to start drawing our wall
        # from, taking into account the difference in thickness
        # between the base and wall and how long our legs will be
        core_triangles_1 = calculate_corner_wall_triangles(
            leg_1_len,
            inner_len,
            thickness_diff / 2,
            angle)
        
        move_cursor_to_wall_start(
            core_triangles_1,
            angle,
            thickness_diff / 2,
            base_height)
        
        core_x_leg = core_triangles_1['b_adj']
        core_y_leg = core_triangles_1['d_adj']
       
        core, vert_locs = draw_u_3D(core_y_leg, core_y_leg, wall_thickness, wall_height - base_height, core_x_leg, True)
        
        core.name = tile_props.tile_name + '.core'
        obj_props = core.mt_object_props
        obj_props.is_mt_object = True
        obj_props.tile_name = tile_props.tile_name
        
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
