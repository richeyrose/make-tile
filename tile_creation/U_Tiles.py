import os
from math import radians
from mathutils import kdtree, Vector
import bpy
import bmesh
from bpy.types import Panel, Operator
from ..lib.bmturtle.commands import (
    pd,
    pu,
    create_turtle,
    add_vert,
    fd,
    rt,
    ri,
    lt,
    up,
    home,
    finalise_turtle)
from ..lib.bmturtle.helpers import (
    bm_select_all,
    bm_deselect_all,
    assign_verts_to_group,
    select_verts_in_bounds,
    bm_shortest_path)
from .. lib.utils.utils import mode, get_all_subclasses
from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
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

        if leg_1_outer_len < 4 and leg_1_outer_len >= 1:
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

        if leg_2_outer_len < 4 and leg_2_outer_len >= 1:
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

    subdivs = {
        'leg_1': tile_props.leg_1_native_subdivisions,
        'leg_2': tile_props.leg_2_native_subdivisions,
        'x': tile_props.x_native_subdivisions,
        'width': tile_props.y_native_subdivisions,
        'height': tile_props.z_native_subdivisions}

    dimensions = {
        'leg_1_inner': tile_props.leg_1_len,
        'leg_2_inner': tile_props.leg_2_len,
        'base_height': tile_props.base_size[2],
        'height': tile_props.tile_size[2] - tile_props.base_size[2],
        'x_inner': tile_props.tile_size[0],
        'thickness': tile_props.tile_size[1],
        'thickness_diff': tile_props.base_size[1] - tile_props.tile_size[1]}

    core = draw_u_wall_core(dimensions, subdivs, margin=0.001)

    core.name = tile_props.tile_name + '.core'
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    #create_vertex_groups(core, vert_locs, native_subdivisions)

    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core],
        'selected_editable_objects': [core]
    }

    mode('OBJECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    return core


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
    dimensions = {
        'leg 1 inner': tile_props.leg_1_len,
        'leg 2 inner': tile_props.leg_2_len,
        'thickness': tile_props.base_size[1],
        'height': tile_props.base_size[2],
        'x inner': tile_props.tile_size[0]}

    base = draw_plain_u_base(dimensions)

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


def draw_plain_u_base(dimensions):
    """Return a plain U shaped Base.

    Args:
        dimensions (dict{
        'leg 1 inner': float,
        'leg 2 inner': float,
        'thickness': float,
        'height': float,
        'x inner': float}): dimensions of base

    Returns:
        bpy.types.Object: Base object
    """
    leg_1_inner = dimensions['leg 1 inner']
    leg_2_inner = dimensions['leg 2 inner']
    x_inner = dimensions['x inner']
    thickness = dimensions['thickness']
    height = dimensions['height']

    leg_1_outer = leg_1_inner + thickness
    leg_2_outer = leg_2_inner + thickness
    x_outer = x_inner + (thickness * 2)

    bm, obj = create_turtle('U Base')
    bm.select_mode = {'VERT'}

    pd(bm)
    add_vert(bm)

    fd(bm, leg_1_outer)
    rt(90)
    fd(bm, thickness)
    rt(90)
    fd(bm, leg_1_inner)
    lt(90)
    fd(bm, x_inner)
    lt(90)
    fd(bm, leg_2_inner)
    rt(90)
    fd(bm, thickness)
    rt(90)
    fd(bm, leg_2_outer)
    rt(90)
    fd(bm, x_outer)
    bm_select_all(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=True, edges=bm.edges, normal=(0, 0, -1))
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)
    home(obj)
    finalise_turtle(bm, obj)
    return obj


def draw_u_core(dimensions, subdivs, margin=0.001):
    """Draw a U shaped Core

    Args:
        dimensions (dict{
        'leg_1_inner': float,
        'leg_2_inner': float,
        'base_height': float,
        'height': float,
        'x_inner': float,
        'thickness': float,
        'thickness_diff': float}): core dimensions
        subdivs (dict{
            leg_1: int,
            leg_2: int,
            x: int,
            width: int,
            height: int}): subdivisions
        margin (float, optional): Margin to leave around textured areas
        to correct for displacement distortion.
        Defaults to 0.001.

    Returns:
        bmesh: bmesh
        bpy.types.Object: bmesh owning object
        BMVerts.layers.deform: deform groups
        dict{
            'Leg 1 Inner': list[Vector(3)]
            'Leg 2 Inner': list[Vector(3)]
            'Leg 1 Outer': list[Vector(3)]
            'Leg 2 Outer': list[Vector(3)]
            'Leg 1 End': list[Vector(3)]
            'Leg 2 End': list[Vector(3)]
            'End Wall Inner': list[Vector(3)]
            'End Wall Outer': list[Vector(3)]}: vertex locations
    """
    thickness = dimensions['thickness']
    thickness_diff = dimensions['thickness_diff']

    leg_1_inner = dimensions['leg_1_inner'] + (thickness_diff / 2)
    leg_2_inner = dimensions['leg_2_inner'] + (thickness_diff / 2)
    leg_1_outer = leg_1_inner + thickness
    leg_2_outer = leg_2_inner + thickness

    x_inner = dimensions['x_inner'] + thickness_diff
    x_outer = x_inner + (thickness * 2)

    height = dimensions['height']
    base_height = dimensions['base_height']

    vert_groups = [
        'Leg 1 End',
        'Leg 2 End',
        'Leg 1 Inner',
        'Leg 2 Inner',
        'End Wall Inner',
        'End Wall Outer',
        'Leg 1 Outer',
        'Leg 2 Outer',
        'Leg 1 Top',
        'Leg 2 Top',
        'End Wall Top',
        'Leg 1 Bottom',
        'Leg 2 Bottom',
        'End Wall Bottom']

    bm, obj = create_turtle('U core', vert_groups)
    verts = bm.verts
    verts.layers.deform.verify()
    deform_groups = verts.layers.deform.active

    leg_1_outer_vert_locs = []
    leg_1_inner_vert_locs = []
    leg_1_end_vert_locs = []

    x_outer_vert_locs = []
    x_inner_vert_locs = []

    leg_2_outer_vert_locs = []
    leg_2_inner_vert_locs = []
    leg_2_end_vert_locs = []

    # move cursor to start
    pu(bm)
    up(bm, base_height)
    fd(bm, thickness_diff / 2)
    ri(bm, thickness_diff / 2)
    pd(bm)

    # draw leg 1 outer
    subdiv_dist = (leg_1_outer - margin) / subdivs['leg_1']

    bm.select_mode = {'VERT'}
    add_vert(bm)
    verts.ensure_lookup_table()
    leg_1_outer_vert_locs.append(verts[-1].co.copy())

    bm.verts.ensure_lookup_table()
    start_index = verts[-1].index
    i = 0
    while i < subdivs['leg_1']:
        fd(bm, subdiv_dist)
        i += 1
    fd(bm, margin)

    bm.verts.ensure_lookup_table()
    i = start_index
    while i <= verts[-1].index:
        leg_1_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    # draw leg 1 end
    # we will bride inner and outer sides so we dont draw end edges
    bm.verts.ensure_lookup_table()
    leg_1_end_vert_locs.append(verts[-1].co.copy())
    pu(bm)
    rt(90)
    fd(bm, thickness)
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_1_end_vert_locs.append(verts[-1].co.copy())
    rt(90)

    # leg 1 inner
    subdiv_dist = (leg_1_inner - margin) / subdivs['leg_1']
    start_index = verts[-1].index
    fd(bm, margin)

    i = 0
    while i < subdivs['leg_1']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_1_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    # x inner
    subdiv_dist = (x_inner) / subdivs['x']
    start_index = verts[-1].index

    lt(90)

    i = 0
    while i < subdivs['x']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        x_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    # leg 2 inner
    subdiv_dist = (leg_2_inner - margin) / subdivs['leg_2']
    start_index = verts[-1].index

    lt(90)

    i = 0
    while i < subdivs['leg_2']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_2_inner_vert_locs.append(verts[i].co.copy())
        i += 1

    fd(bm, margin)
    bm.verts.ensure_lookup_table()
    leg_2_inner_vert_locs.append(verts[-1].co.copy())

    #leg 2 end
    leg_2_end_vert_locs.append(verts[-1].co.copy())
    pu(bm)
    rt(90)
    fd(bm, thickness)
    pd(bm)
    add_vert(bm)
    bm.verts.ensure_lookup_table()
    leg_2_end_vert_locs.append(verts[-1].co.copy())

    # leg 2 outer
    subdiv_dist = (leg_2_outer - margin) / subdivs['leg_2']
    rt(90)

    start_index = verts[-1].index
    fd(bm, margin)
    i = 0
    while i < subdivs['leg_2']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    bm.verts.ensure_lookup_table()
    while i <= verts[-1].index:
        leg_2_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    # x outer
    subdiv_dist = x_outer / subdivs['x']
    rt(90)

    start_index = verts[-1].index

    i = 0
    while i < subdivs['x']:
        fd(bm, subdiv_dist)
        i += 1

    i = start_index
    verts.ensure_lookup_table()
    while i <= verts[-1].index:
        x_outer_vert_locs.append(verts[i].co.copy())
        i += 1

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    ret = bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bmesh.ops.subdivide_edges(bm, edges=ret['edges'], smooth=1, smooth_falloff='LINEAR', cuts=subdivs['width'])

    bmesh.ops.inset_region(bm, faces=bm.faces, use_even_offset=True, thickness=margin, use_boundary=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=margin / 2)

    # Z
    subdiv_dist = (height - (margin * 2)) / subdivs['height']
    bm_select_all(bm)
    bm.select_mode = {'FACE'}

    up(bm, margin, False)

    i = 0
    while i < subdivs['height']:
        up(bm, subdiv_dist)
        i += 1
    up(bm, margin)

    home(obj)

    vert_locs = {
        'Leg 1 Inner': leg_1_inner_vert_locs,
        'Leg 2 Inner': leg_2_inner_vert_locs,
        'Leg 1 Outer': leg_1_outer_vert_locs,
        'Leg 2 Outer': leg_2_outer_vert_locs,
        'Leg 1 End': leg_1_end_vert_locs,
        'Leg 2 End': leg_2_end_vert_locs,
        'End Wall Inner': x_inner_vert_locs,
        'End Wall Outer': x_outer_vert_locs}

    return bm, obj, deform_groups, vert_locs


def draw_u_wall_core(dimensions, subdivs, margin=0.001):
    """Return a U wall core

    Args:
        dimensions (dict{
            'leg_1_inner': float,
            'leg_2_inner': float,
            'base_height': float,
            'height': float,
            'x_inner': float,
            'thickness': float,
            'thickness_diff': float}): core dimensions
        subdivs (dict{
            leg_1: int,
            leg_2: int,
            x: int,
            width: int,
            height: int}): subdivisions
        margin (float, optional): Margin to leave around textured areas
        to correct for displacement distortion.
        Defaults to 0.001.

    Returns:
        bpy.types.Object: core
    """
    bm, core, deform_groups, vert_locs = draw_u_core(dimensions, subdivs, margin)
    vert_groups = create_u_core_vert_groups_vert_lists_2(bm, dimensions, margin, vert_locs, subdivs)

    blank_groups = [
        'Leg 1 Top',
        'Leg 2 Top',
        'End Wall Top',
        'Leg 1 End',
        'Leg 2 End',
        'Leg 1 Bottom',
        'Leg 2 Bottom',
        'End Wall Bottom']

    textured_groups = [
        'Leg 1 Inner',
        'Leg 2 Inner',
        'Leg 1 Outer',
        'Leg 2 Outer',
        'End Wall Inner',
        'End Wall Outer']

    blank_group_verts = set()

    for key, value in vert_groups.items():
        if key in blank_groups:
            blank_group_verts = blank_group_verts.union(value)

    for group in textured_groups:
        verts = [v for v in vert_groups[group] if v not in blank_group_verts]
        assign_verts_to_group(verts, core, deform_groups, group)

    for group in blank_groups:
        assign_verts_to_group(vert_groups[group], core, deform_groups, group)

    finalise_turtle(bm, core)
    return core


def create_u_core_vert_groups_vert_lists_2(bm, dimensions, margin, vert_locs, subdivs):
    """Create vertex group vertex lists for U core sides

    Args:
        bm (bmesh): bmesh
        dimensions (dict{
            leg_1_inner: float,
            leg_2_inner: float,
            base_height: float,
            height: float,
            x_inner: float,
            thickness: float,
            thickness_diff: float}): core dimensions
        margin (float): margin between textured and blank areas
        vert_locs (dict{
            Leg 1 Inner: list[Vector(3)]
            Leg 2 Inner: list[Vector(3)]
            Leg 1 Outer: list[Vector(3)]
            Leg 2 Outer: list[Vector(3)]
            Leg 1 End: list[Vector(3)]
            Leg 2 End: list[Vector(3)]
            End Wall Inner': list[Vector(3)]
            End Wall Outer': list[Vector(3)]}: vertex locations
        subdivs (dict{
            leg_1: int,
            leg_2: int,
            x: int,
            width: int,
            height: int}): subdivisions

    Returns:
        dict{
            Leg 1 Inner: list[BMVert],
            Leg 1 Outer: list[BMVert],
            Leg 2 Inner: list[BMVert],
            Leg 2 Outer: list[BMVert],
            Leg 1 Top: list[BMVert],
            Leg 2 Top: list[BMVert],
            Leg 1 Bottom: list[BMVert],
            Leg 2 Bottom: list[BMVert],
            Leg 1 End: list[BMVert],
            Leg 2 End: list[BMVert],
            End Wall Inner: list[BMVert],
            End Wall Outer: list[BMVert],
            End Wall Top: list[BMVert]
            End Wall Bottom: list[BMVert]}: Verts to assign to vert groups
    """
    height = dimensions['height']
    thickness_diff = dimensions['thickness_diff']
    thickness = dimensions['thickness']
    leg_1_inner_len = dimensions['leg_1_inner'] + (thickness_diff / 2)
    leg_2_inner_len = dimensions['leg_2_inner'] + (thickness_diff / 2)
    leg_1_outer_len = leg_1_inner_len + thickness
    leg_2_outer_len = leg_2_inner_len + thickness

    vert_groups = {}

    # create kdtree
    size = len(bm.verts)
    kd = kdtree.KDTree(size)

    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)

    kd.balance()

    # leg_sides
    leg_sides = {
        'Leg 1 Inner': (vert_locs['Leg 1 Inner'][::-1], leg_1_inner_len),
        'Leg 2 Inner': (vert_locs['Leg 2 Inner'], leg_2_inner_len),
        'Leg 1 Outer': (vert_locs['Leg 1 Outer'], leg_1_outer_len),
        'Leg 2 Outer': (vert_locs['Leg 2 Outer'][::-1], leg_2_outer_len)}

    for key, value in leg_sides.items():
        vert_groups[key] = select_verts_in_bounds(
            lbound=(value[0][0]),
            ubound=(value[0][-1][0], value[0][-1][1] + value[1], value[0][-1][2] + height),
            buffer=margin / 2,
            bm=bm)

    end_wall_sides = {
        'End Wall Inner': vert_locs['End Wall Inner'],
        'End Wall Outer': vert_locs['End Wall Outer'][::-1]}

    # end_wall_sides
    for key, value in end_wall_sides.items():
        vert_groups[key] = select_verts_in_bounds(
            lbound=(value[0]),
            ubound=(value[-1][0], value[-1][1], value[-1][2] + height),
            buffer=margin / 2,
            bm=bm)

    # leg ends
    ends = {
        'Leg 1 End': vert_locs['Leg 1 End'],
        'Leg 2 End': vert_locs['Leg 2 End']}

    for key, value in ends.items():
        vert_groups[key] = select_verts_in_bounds(
            lbound=(value[0]),
            ubound=(value[1][0], value[1][1], value[1][2] + height),
            buffer=margin / 2,
            bm=bm)
    bm_deselect_all(bm)

    # bottom
    # leg 1
    inner_locs = vert_locs['Leg 1 Inner'][::-1]
    outer_locs = vert_locs['Leg 1 Outer']

    selected_verts = []
    i = 0
    while i < len(outer_locs) and i < len(inner_locs):
        v1_co, v1_index, dist = kd.find(inner_locs[i])
        v2_co, v2_index, dist = kd.find(outer_locs[i])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts.extend(verts)
        i += 1

    vert_groups['Leg 1 Bottom'] = selected_verts
    bm_deselect_all(bm)

    # leg 2
    inner_locs = vert_locs['Leg 2 Inner'][::-1]
    outer_locs = vert_locs['Leg 2 Outer']

    selected_verts = []
    i = 0
    while i < len(inner_locs) and i < len(outer_locs):
        v1_co, v1_index, dist = kd.find(inner_locs[i])
        v2_co, v2_index, dist = kd.find(outer_locs[i])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts.extend(verts)
        i += 1
    vert_groups['Leg 2 Bottom'] = selected_verts

    # end wall
    inner_locs = vert_locs['End Wall Inner'][::-1]
    outer_locs = vert_locs['End Wall Outer']

    selected_verts = []
    i = 0
    while i < len(inner_locs) and i < len(outer_locs):
        v1_co, v1_index, dist = kd.find(inner_locs[i])
        v2_co, v2_index, dist = kd.find(outer_locs[i])

        bm.verts.ensure_lookup_table()
        v1 = bm.verts[v1_index]
        v2 = bm.verts[v2_index]

        nodes = bm_shortest_path(bm, v1, v2)
        node = nodes[v2]

        for e in node.shortest_path:
            e.select_set(True)
        bm.select_flush(True)

        verts = [v for v in bm.verts if v.select]
        selected_verts.extend(verts)
        i += 1
    vert_groups['End Wall Bottom'] = selected_verts

    # top
    vert_groups['Leg 1 Top'] = []
    vert_groups['Leg 2 Top'] = []
    vert_groups['End Wall Top'] = []

    bm.verts.ensure_lookup_table()
    for v in vert_groups['Leg 1 Bottom']:
        v_co, v_index, dist = kd.find((v.co[0], v.co[1], v.co[2] + height))
        vert_groups['Leg 1 Top'].append(bm.verts[v_index])

    bm.verts.ensure_lookup_table()
    for v in vert_groups['Leg 2 Bottom']:
        v_co, v_index, dist = kd.find((v.co[0], v.co[1], v.co[2] + height))
        vert_groups['Leg 2 Top'].append(bm.verts[v_index])

    bm.verts.ensure_lookup_table()
    for v in vert_groups['End Wall Bottom']:
        v_co, v_index, dist = kd.find((v.co[0], v.co[1], v.co[2] + height))
        vert_groups['End Wall Top'].append(bm.verts[v_index])

    return vert_groups
