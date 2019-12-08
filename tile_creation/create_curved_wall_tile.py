import os
import bpy
from mathutils import Vector
from math import degrees, radians, pi
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_path, get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.utils import mode, view3d_find
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    load_secondary_material,
    assign_mat_to_vert_group,
    add_displacement_mesh_modifiers,
    add_preview_mesh_modifiers,
    assign_displacement_materials,
    assign_preview_materials)
from .. enums.enums import geometry_types
from . create_straight_wall_tile import (
    create_straight_wall_base,
    create_straight_wall_core,
    create_straight_wall_slab)


def create_curved_wall(tile_name):
    base_thickness = bpy.context.scene.mt_base_y
    base_height = bpy.context.scene.mt_base_z
    base_inner_radius = bpy.context.scene.mt_base_inner_radius
    degrees_of_arc = bpy.context.scene.mt_degrees_of_arc
    segments = bpy.context.scene.mt_segments

    base = create_plain_curved_wall_base(
        base_thickness,
        base_height,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name)


def create_plain_curved_wall_base(base_thickness, base_height, base_inner_radius, degrees_of_arc, segments, tile_name):

    circumference = 2 * pi * base_inner_radius
    base_length = circumference / (360 / degrees_of_arc)

    base = create_straight_wall_base(tile_name, (base_length, base_thickness, base_height))

    deselect_all()
    select(base.name)
    activate(base.name)

    # loopcut base
    mode('EDIT')
    region, rv3d, v3d, area = view3d_find(True)

    override = {
        'scene': bpy.context.scene,
        'region': region,
        'area': area,
        'space': v3d
    }

    bpy.ops.mesh.loopcut(override, number_cuts=segments - 2, smoothness=0, falloff='INVERSE_SQUARE', object_index=0, edge_index=2)

    mode('OBJECT')

    curve_mod = base.modifiers.new("curve", "SIMPLE_DEFORM")
    curve_mod.deform_method = 'BEND'
    curve_mod.deform_axis = 'Z'
    curve_mod.angle = radians(degrees_of_arc)

    return base
