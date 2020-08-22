import os
from math import radians
import bpy
import bmesh
from bpy.types import Panel, Operator
from mathutils import Vector
from .. lib.utils.utils import mode, vectors_are_close, get_all_subclasses
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.utils.selection import (
    deselect_all,
    select)
from .create_tile import (
    create_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg)
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

# leg_1_len and leg_2_len are the inner lengths of the legs
#             ||           ||
#             ||leg_1 leg_2||
#             ||           ||
#             ||___inner___||
#      origin x--------------
#                 outer
#


class MT_PT_U_Tile_Panel(Panel):
    """Draw a tile options panel in the UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_U_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type in [
                "U_WALL"]
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_z', text='Height')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'tile_x', text='End Wall Length')

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'y_proportionate_scale', text="Width")
        row.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text="Width")
        layout.prop(scene_props, 'base_z', text="Height")

        if scene_props.base_blueprint == 'OPENLOCK':
            layout.prop(scene_props, 'base_socket_side', text='Base Socket Side')

        layout.label(text="Native Subdivisions:")

        layout.prop(scene_props, 'leg_1_native_subdivisions')
        layout.prop(scene_props, 'leg_2_native_subdivisions')
        layout.prop(scene_props, 'x_native_subdivisions')
        layout.prop(scene_props, 'y_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_U_Wall_Tile(MT_Tile_Generator, Operator):
    """Create a U Wall Tile."""

    bl_idname = "object.make_u_wall"
    bl_label = "U Wall"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "U_WALL"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'U_BASE'
        core_type = 'U_WALL_CORE'

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_wall_creator(
            context, scene_props)
        subclasses = get_all_subclasses(MT_Tile_Generator)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer
        return {'FINISHED'}


class MT_OT_Make_Openlock_U_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK U base."""

    bl_idname = "object.make_openlock_u_base"
    bl_label = "OpenLOCK U Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "U_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_U_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain u base."""

    bl_idname = "object.make_plain_u_base"
    bl_label = "Plain U Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "U_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_U_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty u base."""

    bl_idname = "object.make_empty_u_base"
    bl_label = "Empty U Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "U_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_U_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain u wall core."""

    bl_idname = "object.make_plain_u_wall_core"
    bl_label = "U Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "U_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_plain_wall_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_U_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock u wall core."""

    bl_idname = "object.make_openlock_u_wall_core"
    bl_label = "U Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "U_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        spawn_openlock_wall_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_U_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved wall core."""

    bl_idname = "object.make_empty_u_wall_core"
    bl_label = "U Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "U_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def spawn_openlock_wall_cores(base, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'End Wall Inner', 'End Wall Outer', 'Leg 2 Inner', 'Leg 2 Outer']
    preview_core = spawn_core(tile_props)

    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)

    cores = [preview_core, displacement_core]

    cutters = spawn_openlock_wall_cutters(base, tile_props)

    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props)

        for core in cores:
            set_bool_props(cutter, core, 'DIFFERENCE')

    if tile_props.tile_size[0] >= 1:
        pegs = spawn_openlock_top_pegs(core, tile_props)

        for peg in pegs:
            set_bool_obj_props(peg, base, tile_props)

            for core in cores:
                set_bool_props(peg, core, 'UNION')

    displacement_core.hide_viewport = True
    return preview_core


def spawn_openlock_wall_cutters(base, tile_props):
    """Spawn OpenLOCK wall cores into scene and position them.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    preferences = get_prefs()
    tile_name = tile_props.tile_name

    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    for obj in data_to.objects:
        add_object_to_collection(obj, tile_name)

    cutter = data_to.objects[0]

    array_mod = cutter.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.fit_type = 'FIT_LENGTH'

    tile_size = tile_props.tile_size
    leg_1_inner_len = tile_props.leg_1_len
    leg_2_inner_len = tile_props.leg_2_len
    x_inner_len = tile_props.base_size[0]
    thickness = tile_props.base_size[1]

    leg_1_outer_len = leg_1_inner_len + thickness
    leg_2_outer_len = leg_2_inner_len + thickness
    x_outer_len = x_inner_len + (thickness * 2)

    leg_1_bottom_cutter = cutter
    leg_1_bottom_cutter.location = base.location
    leg_1_bottom_cutter.name = 'Leg 1 Bottom.cutter.' + tile_props.tile_name

    leg_1_top_cutter = leg_1_bottom_cutter.copy()
    leg_1_top_cutter.data = leg_1_top_cutter.data.copy()
    leg_1_top_cutter.name = 'Leg 1 Top.cutter.' + tile_props.tile_name

    leg_2_bottom_cutter = leg_1_bottom_cutter.copy()
    leg_2_bottom_cutter.data = leg_2_bottom_cutter.data.copy()
    leg_2_bottom_cutter.name = 'Leg 2 Bottom.cutter.' + tile_props.tile_name

    leg_2_top_cutter = leg_1_bottom_cutter.copy()
    leg_2_top_cutter.data = leg_2_top_cutter.data.copy()
    leg_2_top_cutter.name = 'Leg 2 Top.cutter.' + tile_props.tile_name

    cutters = [
        leg_1_bottom_cutter,
        leg_1_top_cutter,
        leg_2_bottom_cutter,
        leg_2_top_cutter]

    for cutter in cutters:
        add_object_to_collection(cutter, tile_props.tile_name)
        cutter.rotation_euler[2] = radians(-90)

    leg_1_cutters = [leg_1_bottom_cutter, leg_1_top_cutter]
    leg_2_cutters = [leg_2_bottom_cutter, leg_2_top_cutter]
    bottom_cutters = [leg_1_bottom_cutter, leg_2_bottom_cutter]
    top_cutters = [leg_1_top_cutter, leg_2_top_cutter]

    for cutter in leg_1_cutters:
        cutter.location = (cutter.location[0] + 0.25, cutter.location[1] + leg_1_outer_len, cutter.location[2])

    for cutter in leg_2_cutters:
        cutter.location = (cutter.location[0] + x_outer_len - 0.25, cutter.location[1] + leg_2_outer_len, cutter.location[2])

    for cutter in bottom_cutters:
        cutter.location[2] = cutter.location[2] + 0.63
        array_mod = cutter.modifiers['Array']
        array_mod.constant_offset_displace[2] = 2
        array_mod.fit_length = tile_size[2] - 1

    for cutter in top_cutters:
        cutter.location[2] = cutter.location[2] + 1.38
        array_mod = cutter.modifiers['Array']
        array_mod.constant_offset_displace[2] = 2
        array_mod.fit_length = tile_size[2] - 1.8

    return cutters


def spawn_openlock_top_pegs(core, tile_props):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        core (bpy.types.Object): tile core
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """

    tile_size = tile_props.tile_size
    base_size = tile_props.base_size
    leg_1_inner_len = tile_props.leg_1_len
    leg_2_inner_len = tile_props.leg_2_len
    x_inner_len = tile_props.base_size[0]
    thickness = tile_props.base_size[1]

    leg_1_outer_len = leg_1_inner_len + thickness
    leg_2_outer_len = leg_2_inner_len + thickness
    x_outer_len = x_inner_len + (thickness * 2)

    cursor = bpy.context.scene.cursor

    peg = load_openlock_top_peg(tile_props)
    peg.name = 'Base Wall Top Peg.' + tile_props.tile_name

    array_mod = peg.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[0] = 0.505
    array_mod.fit_type = 'FIXED_COUNT'
    array_mod.count = 2

    core_location = core.location.copy()

    pegs = []

    # Back wall
    if x_outer_len < 4 and x_outer_len >= 1:
        peg.location = (
            core_location[0] + (x_outer_len / 2) - 0.252,
            core_location[1] + (base_size[1] / 2) + 0.08,
            core_location[2] + tile_size[2])
    else:
        peg.location = (
            core_location[0] + 0.756 + thickness,
            core_location[1] + (base_size[1] / 2) + 0.08,
            core_location[2] + tile_size[2])
        array_mod = peg.modifiers.new('Array', 'ARRAY')
        array_mod.use_relative_offset = False
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace[0] = 2.017
        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_size[0] - 1.3

    pegs.append(peg)

    # leg 1
    if leg_1_outer_len >= 1:
        peg_2 = load_openlock_top_peg(tile_props)
        peg_2.name = 'Leg 1 Top Peg.' + tile_props.tile_name

        peg_2.rotation_euler[2] = radians(-90)
        ctx = {
            'object': peg_2,
            'active_object': peg_2,
            'selected_objects': [peg_2],
            'selectable_objects': [peg_2],
            'selected_editable_objects': [peg_2]
        }

        bpy.ops.object.transform_apply(
            ctx,
            location=False,
            rotation=True,
            scale=False,
            properties=True)

        if leg_1_outer_len < 4 and leg_1_outer_len >=1:
            peg_2.location = (
                core_location[0] + (thickness / 2) + 0.08,
                core_location[1] + (leg_1_outer_len / 2) - 0.252,
                core_location[2] + tile_size[2])
        else:
            peg_2.location = (
                core_location[0] + (thickness / 2) + 0.08,
                core_location[0] + 0.756 + thickness,
                core_location[2] + tile_size[2])

        if leg_1_outer_len >= 2:
            array_mod = peg_2.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 0.505
            array_mod.fit_type = 'FIXED_COUNT'
            array_mod.count = 2

        if leg_1_outer_len >= 4:
            array_mod = peg_2.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 2.017
            array_mod.fit_type = 'FIT_LENGTH'
            array_mod.fit_length = leg_1_outer_len - 1.3

        pegs.append(peg_2)

    # leg 2
    if leg_2_outer_len >= 1:
        peg_3 = load_openlock_top_peg(tile_props)
        peg_3.name = 'Leg 2 Top Peg.' + tile_props.tile_name

        peg_3.rotation_euler[2] = radians(90)
        ctx = {
            'object': peg_3,
            'active_object': peg_3,
            'selected_objects': [peg_3],
            'selectable_objects': [peg_3],
            'selected_editable_objects': [peg_3]
        }

        bpy.ops.object.transform_apply(
            ctx,
            location=False,
            rotation=True,
            scale=False,
            properties=True)

        if leg_2_outer_len < 4 and leg_2_outer_len >=1:
            peg_3.location = (
                core_location[0] + x_outer_len - (thickness / 2) - 0.08,
                core_location[1] + (leg_2_outer_len / 2) - 0.252,
                core_location[2] + tile_size[2])
        else:
            peg_3.location = (
                core_location[0] + x_outer_len - (thickness / 2) - 0.08,
                core_location[0] + 0.756 + thickness,
                core_location[2] + tile_size[2])

        if leg_2_outer_len >= 2:
            array_mod = peg_3.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 0.505
            array_mod.fit_type = 'FIXED_COUNT'
            array_mod.count = 2

        if leg_2_outer_len >= 4:
            array_mod = peg_3.modifiers.new('Array', 'ARRAY')
            array_mod.use_relative_offset = False
            array_mod.use_constant_offset = True
            array_mod.constant_offset_displace[1] = 2.017
            array_mod.fit_type = 'FIT_LENGTH'
            array_mod.fit_length = leg_2_outer_len - 1.3

        pegs.append(peg_3)

    return pegs

    # End wall


def spawn_plain_wall_cores(base, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_core(tile_props)
    textured_vertex_groups = ['Leg 1 Outer', 'Leg 1 Inner', 'End Wall Inner', 'End Wall Outer', 'Leg 2 Inner', 'Leg 2 Outer']
    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    return preview_core


def spawn_core(tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
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
        tile_props.y_native_subdivisions,
        tile_props.z_native_subdivisions)

    core, vert_locs = draw_core(
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

    create_vertex_groups(core, vert_locs, native_subdivisions)

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


def draw_core(leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height, native_subdivisions, thickness_diff):
    """Draw a u shaped core

    Args:
        leg_1_inner_len (float): length
        leg_2_inner_len (flot): length
        x_inner_len (float): length
        thickness (float): width
        z_height (float): height
        native_subdivisions (list): subdivisions
        thickness_diff (float): difference between base and core thickness

    Returns:
        bpy.types.Object: core
        list: vertex locations


                ||           ||
                ||leg_1 leg_2||
                ||           ||
                ||___inner___||
        origin x--------------
                    outer
    """

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
    ctx = {'object': obj,
           'active_object': obj,
           'selected_objects': [obj]
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


def create_vertex_groups(obj, vert_locs, native_subdivisions):
    """Create vertex groups

    Args:
        obj (bpy.types.Object): tile core
        vert_locs (dict): vertex locations
        native_subdivisions (list): subdivisions
    """
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
                if vectors_are_close(v.co, coord, 0.0001):
                    v.select = True
                    break

        for index, coord in enumerate(vert_coords):
            vert_coords[index] = Vector((0, 0, 0.001)) + coord

        for coord in vert_coords:
            for v in bm.verts:
                if vectors_are_close(v.co, coord, 0.0001):
                    v.select = True
                    break

        i = 0
        while i <= native_subdivisions[4]:
            for index, coord in enumerate(vert_coords):
                vert_coords[index] = Vector((0, 0, subdiv_dist)) + coord

            for coord in vert_coords:
                for v in bm.verts:
                    if vectors_are_close(v.co, coord, 0.0001):
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
                if vectors_are_close(v.co, coord, 0.0001):
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
                if vectors_are_close(v.co, coord, 0.0001):
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
                    if vectors_are_close(v.co, coord, 0.0001):
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
                if vectors_are_close(v.co, coord, 0.0001):
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
    inner_vert_locs = vert_locs['Leg 2 Inner']
    outer_vert_locs = vert_locs['Leg 2 Outer'][::-1]

    for v in bm.verts:
        v.select = False

    i = 0
    while i < len(inner_vert_locs):
        for v in bm.verts:
            if vectors_are_close(v.co, outer_vert_locs[i], 0.0001):
                v.select = True
                break

        for v in bm.verts:
            if vectors_are_close(v.co, inner_vert_locs[i], 0.0001):
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

    bmesh.update_edit_mesh(bpy.context.object.data)

    mode('OBJECT')


def initialise_wall_creator(context, scene_props):
    """Initialise the wall creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (MakeTile.properties.MT_Scene_Properties): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Walls', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Walls'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'U_WALL'
    tile_props.leg_1_len = scene_props.leg_1_len
    tile_props.leg_2_len = scene_props.leg_2_len
    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)
    tile_props.base_socket_side = scene_props.base_socket_side

    tile_props.leg_1_native_subdivisions = scene_props.leg_1_native_subdivisions
    tile_props.leg_2_native_subdivisions = scene_props.leg_2_native_subdivisions
    tile_props.x_native_subdivisions = scene_props.x_native_subdivisions
    tile_props.y_native_subdivisions = scene_props.y_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    leg_1_inner_len = tile_props.leg_1_len
    leg_2_inner_len = tile_props.leg_2_len
    thickness = tile_props.base_size[1]
    z_height = tile_props.base_size[2]
    x_inner_len = tile_props.tile_size[0]

    base = draw_plain_base(leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height)

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn OpenLOCK base into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base
    """
    tile_props.base_size = Vector((tile_props.tile_size[0], 0.5, 0.2755))
    base_socket_side = tile_props.base_socket_side
    leg_1_inner_len = tile_props.leg_1_len
    leg_2_inner_len = tile_props.leg_2_len
    x_inner_len = tile_props.base_size[0]
    thickness = tile_props.base_size[1]

    leg_1_outer_len = leg_1_inner_len + thickness
    leg_2_outer_len = leg_2_inner_len + thickness
    x_outer_len = x_inner_len + (thickness * 2)

    base = spawn_plain_base(tile_props)

    # create base slot cutter
    slot_cutter = spawn_openlock_base_slot_cutter(tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props)
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    # clip cutters
    clip_cutter_leg_1 = spawn_openlock_base_clip_cutter(tile_props)
    clip_cutter_leg_1.name = 'Leg 1 Clip.' + tile_props.name + '.clip_cutter'
    clip_cutter_leg_2 = clip_cutter_leg_1.copy()
    clip_cutter_leg_2.name = 'Leg 2 Clip.' + tile_props.name + '.clip_cutter'
    clip_cutter_leg_2.data = clip_cutter_leg_2.data.copy()
    clip_cutter_x_leg = clip_cutter_leg_1.copy()
    clip_cutter_x_leg.name = 'End Wall Clip.' + tile_props.name + '.clip_cutter'
    clip_cutter_x_leg.data = clip_cutter_x_leg.data.copy()

    cutters = [clip_cutter_leg_1, clip_cutter_leg_2, clip_cutter_x_leg]

    for cutter in cutters:
        add_object_to_collection(cutter, tile_props.tile_name)
        set_bool_obj_props(cutter, base, tile_props)
        set_bool_props(cutter, base, 'DIFFERENCE')

    if base_socket_side == 'INNER':
        clip_cutter_leg_1.rotation_euler = (clip_cutter_leg_1.rotation_euler[0], clip_cutter_leg_1.rotation_euler[1], radians(90))
        clip_cutter_leg_1.location = (clip_cutter_leg_1.location[0] + 0.25, thickness * 2, clip_cutter_leg_1.location[2])
        clip_cutter_leg_1.modifiers['Array'].fit_length = leg_1_inner_len - 1

        clip_cutter_x_leg.rotation_euler = (clip_cutter_x_leg.rotation_euler[0], clip_cutter_x_leg.rotation_euler[1], radians(180))
        clip_cutter_x_leg.location = (x_inner_len, 0.25, clip_cutter_x_leg.location[2])
        clip_cutter_x_leg.modifiers['Array'].fit_length = x_inner_len - 1

        clip_cutter_leg_2.rotation_euler = (clip_cutter_leg_2.rotation_euler[0], clip_cutter_leg_2.rotation_euler[1], radians(-90))
        clip_cutter_leg_2.location = (x_inner_len + thickness + 0.25, leg_2_inner_len, clip_cutter_leg_2.location[2])
        clip_cutter_leg_2.modifiers['Array'].fit_length = leg_2_inner_len - 1
    else:
        clip_cutter_leg_1.rotation_euler[2] = radians(-90)
        clip_cutter_leg_1.location = (clip_cutter_leg_1.location[0] + 0.25, clip_cutter_leg_1.location[1] + leg_1_outer_len - 0.5, clip_cutter_leg_1.location[2])
        clip_cutter_leg_1.modifiers['Array'].fit_length = leg_1_outer_len - 1

        clip_cutter_x_leg.location = (clip_cutter_x_leg.location[0] + 0.5, clip_cutter_x_leg.location[1] + 0.25, clip_cutter_x_leg.location[2])
        clip_cutter_x_leg.modifiers['Array'].fit_length = x_outer_len - 1

        clip_cutter_leg_2.rotation_euler[2] = radians(90)
        clip_cutter_leg_2.location = (clip_cutter_leg_2.location[0] + x_outer_len - 0.25, clip_cutter_leg_2.location[1] + 0.5, clip_cutter_leg_2.location[2])
        clip_cutter_leg_2.modifiers['Array'].fit_length = leg_2_outer_len - 1
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(tile_props):
    """Spawn base slot cutter into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base clip cutter
    """
    leg_1_inner_len = tile_props.leg_1_len
    leg_2_inner_len = tile_props.leg_2_len
    x_inner_len = tile_props.tile_size[0]
    thickness = tile_props.base_size[1]

    leg_1_outer_len = leg_1_inner_len + thickness
    leg_2_outer_len = leg_2_inner_len + thickness

    base_socket_side = tile_props.base_socket_side

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

    # The slot cutter is a 0.1 wide rectangle with an array modifier
    slot_cutter = data_to.objects[0]
    slot_cutter.name = 'Base Slot.' + tile_props.tile_name + '.slot_cutter'

    # the start and end caps are both made of objects with their own modifier
    cutter_start_cap = data_to.objects[1]
    cutter_end_cap = data_to.objects[2]

    if base_socket_side == 'OUTER':
        # gap between slot end and side
        slot_end_gap = 0.246

        # main cutter array
        array_mod = slot_cutter.modifiers['Array']
        array_mod.fit_length = x_inner_len - 0.01

        # start piece array
        array_mod = cutter_start_cap.modifiers['Array']
        array_mod.fit_length = leg_1_inner_len - slot_end_gap

        # end piece array
        array_mod = cutter_end_cap.modifiers['Array']
        array_mod.fit_length = leg_2_inner_len - slot_end_gap

        slot_cutter.hide_viewport = False

    else:
        offset = Vector((-0.1529, -0.1529, 0))
        slot_cutter.location = slot_cutter.location + offset

        # gap between slot end and side
        slot_end_gap = 0.246

        # main cutter array
        array_mod = slot_cutter.modifiers['Array']
        array_mod.fit_length = x_inner_len - 0.01 + 0.1529 * 2

        # start piece array
        array_mod = cutter_start_cap.modifiers['Array']
        array_mod.fit_length = leg_1_outer_len - slot_end_gap - 0.1529

        # end piece array
        array_mod = cutter_end_cap.modifiers['Array']
        array_mod.fit_length = leg_2_outer_len - slot_end_gap - 0.1529

        slot_cutter.hide_viewport = True
    return slot_cutter


def spawn_openlock_base_clip_cutter(tile_props):
    """Spawn base clip cutter into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base clip cutter
    """
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

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True
    array_mod.fit_type = 'FIT_LENGTH'

    clip_cutter.hide_viewport = True

    return clip_cutter


def draw_plain_base(leg_1_inner_len, leg_2_inner_len, x_inner_len, thickness, z_height):
    """Draw a u shaped base

    Args:
        leg_1_inner_len (float): length
        leg_2_inner_len (flot): length
        x_inner_len (float): length
        thickness (float): width
        z_height (float): height

    Returns:
        bpy.types.Object: base


                ||           ||
                ||leg_1 leg_2||
                ||           ||
                ||___inner___||
        origin x--------------
                    outer
    """
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
