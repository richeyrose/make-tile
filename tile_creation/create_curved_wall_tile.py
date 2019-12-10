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
    create_wall_slabs)


def create_curved_wall(
        tile_blueprint,
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        tile_material,
        base_inner_radius,
        wall_inner_radius,
        degrees_of_arc,
        segments):

    base, base_size = create_plain_curved_wall_base(
        base_size,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name)

    wall = create_plain_wall(
        base_size,
        tile_size,
        wall_inner_radius,
        degrees_of_arc,
        segments,
        tile_name,
        tile_material)


def create_curved_wall_slabs(
        tile_name,
        core_size,
        base_size,
        tile_size,
        segments,
        degrees_of_arc,
        tile_material):

    displacement_type = 'NORMAL'

    slabs = create_wall_slabs(
        displacement_type,
        tile_name,
        core_size,
        base_size,
        tile_size,
        tile_material)

    for slab in slabs:
        slab.hide_viewport = False

        add_deform_modifiers(slab, segments, degrees_of_arc)
        select(slab.name)
        if slab['geometry_type'] == 'DISPLACEMENT':
            slab.hide_viewport = True


def add_deform_modifiers(obj, segments, degrees_of_arc):
    deselect_all()
    select(obj.name)
    activate(obj.name)

    # loopcut
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

    curve_mod = obj.modifiers.new("curve", "SIMPLE_DEFORM")
    curve_mod.deform_method = 'BEND'
    curve_mod.deform_axis = 'Z'
    curve_mod.show_render = False
    curve_mod.angle = radians(degrees_of_arc)
    bpy.ops.object.modifier_move_up(modifier=curve_mod.name)


def create_curved_wall_core(tile_name, tile_size, base_size, segments, degrees_of_arc):
    core = create_straight_wall_core(tile_name, tile_size, base_size)
    core_size = core.dimensions.copy()

    add_deform_modifiers(core, segments, degrees_of_arc)

    return core, core_size


def create_plain_wall(
        base_size,
        tile_size,
        wall_inner_radius,
        degrees_of_arc,
        segments,
        tile_name,
        tile_material):

    circumference = 2 * pi * wall_inner_radius
    wall_length = circumference / (360 / degrees_of_arc)
    tile_size = Vector((wall_length, tile_size[1] - 0.1850, tile_size[2]))
    core, core_size = create_curved_wall_core(tile_name, tile_size, base_size, segments, degrees_of_arc)
    create_curved_wall_slabs(tile_name, core_size, base_size, tile_size, segments, degrees_of_arc, tile_material)


def create_plain_curved_wall_base(
        base_size,
        base_inner_radius,
        degrees_of_arc,
        segments,
        tile_name):

    circumference = 2 * pi * base_inner_radius
    base_length = circumference / (360 / degrees_of_arc)
    base_size = Vector((base_length, base_size[1], base_size[2]))

    base = create_straight_wall_base(tile_name, base_size)
    add_deform_modifiers(base, segments, degrees_of_arc)

    return base, base_size
