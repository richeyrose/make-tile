import os
from math import radians
import bpy
from bpy.types import Panel, Operator
from ..operators.maketile import (
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.triangular_tile import (
    draw_plain_triangular_base,
    draw_tri_floor_core,
    draw_openlock_tri_floor_base)
from .. lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)
from .. lib.utils.utils import mode, get_all_subclasses
from .. lib.utils.selection import select, deselect_all, select_by_loc
from .. lib.utils.vertex_groups import (
    get_vert_indexes_in_vert_group,
    remove_verts_from_group)
from .create_tile import (
    create_displacement_core,
    finalise_tile,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props)


class MT_PT_Triangular_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Triangular_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type in ["TRIANGULAR_FLOOR"]
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
        layout.prop(scene_props, 'tile_z', text='Tile Height')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

        layout.label(text="Sync Proportions")
        layout.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text='Base Height')

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Triangular_Floor_Tile(MT_Tile_Generator, Operator):
    """Operator. Create a Triangular Floor Tile."""

    bl_idname = "object.make_triangular_floor"
    bl_label = "Triangle Floor"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "TRIANGULAR_FLOOR"

    def execute(self, context):
        """Execute the operator."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = scene_props.base_blueprint
        core_blueprint = scene_props.main_part_blueprint
        base_type = 'TRIANGULAR_BASE'
        core_type = 'TRIANGULAR_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        original_renderer, cursor_orig_loc, cursor_orig_rot = initialise_floor_creator(context, scene_props)
        base = spawn_prefab(context, subclasses, base_blueprint, base_type)

        if core_type == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type)

        finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

        scene.render.engine = original_renderer

        return {'FINISHED'}


class MT_OT_Make_Openlock_Triangular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK triangular base."""

    bl_idname = "object.make_openlock_triangular_base"
    bl_label = "Triangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "TRIANGULAR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_openlock_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Triangular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain triangular base."""

    bl_idname = "object.make_plain_triangular_base"
    bl_label = "Triangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "TRIANGULAR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_plain_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Triangular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty triangular base."""

    bl_idname = "object.make_empty_triangular_base"
    bl_label = "Triangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "TRIANGULAR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain triangular core."""

    bl_idname = "object.make_plain_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "TRIANGULAR_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        tile = context.collection
        tile_props = tile.mt_tile_props
        base = context.active_object
        create_plain_triangular_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock triangular floor core."""

    bl_idname = "object.make_openlock_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "TRIANGULAR_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        bpy.ops.object.make_plain_triangular_floor_core()
        return{'FINISHED'}


class MT_OT_Make_Empty_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty triangular floor core."""

    bl_idname = "object.make_empty_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "TRIANGULAR_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def initialise_floor_creator(context, scene_props):
    """Initialise the floor creator and set common properties.

    Args:
        context (bpy.context): context
        scene_props (bpy.types.PropertyGroup.mt_scene_props): maketile scene properties

    Returns:
        enum: enum in {'BLENDER_EEVEE', 'CYCLES', 'WORKBENCH'}
        list[3]: cursor original location
        list[3]: cursor original rotation

    """
    original_renderer, tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    # We store tile properties in the mt_tile_props property group of
    # the collection so we can access them from any object in this
    # collection.
    create_collection('Floors', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Floors'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    create_common_tile_props(scene_props, tile_props, tile_collection)

    tile_props.tile_type = 'TRIANGULAR_FLOOR'

    tile_props.leg_1_len = scene_props.leg_1_len
    tile_props.leg_2_len = scene_props.leg_2_len
    tile_props.angle = scene_props.angle
    tile_props.tile_z = scene_props.tile_z
    tile_props.base_z = scene_props.base_z
    tile_props.opposite_native_subdivisions = scene_props.opposite_native_subdivisions
    tile_props.z_native_subdivisions = scene_props.z_native_subdivisions

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)

    return original_renderer, cursor_orig_loc, cursor_orig_rot


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile base
    """
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
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(tile_props):
    """Spawn an OpenLOCK base into the scene.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile base
    """
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

    clip_cutters = spawn_openlock_base_clip_cutters(dimensions, tile_props)

    for clip_cutter in clip_cutters:
        set_bool_obj_props(clip_cutter, base, tile_props)
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    bpy.context.view_layer.objects.active = base
    return base


def spawn_openlock_base_clip_cutters(dimensions, tile_props):
    """Make cutters for the openlock base clips.

    Args:
        base (bpy.types.Object): tile base
        tile_props (mt_tile_props): tile properties

    Returns:
        list[bpy.types.Object]: base clip cutters

    """
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
        clip_cutter_1.name = "Leg 2 Clip."
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
                value=(radians(-dimensions['A'] + 90)),
                orient_axis='Z',
                orient_type='GLOBAL',
                center_override=dimensions['loc_A'])

            deselect_all()

            # cutter 2
            clip_cutter_2 = clip_cutter_1.copy()
            clip_cutter_2.name = "Leg 1 Clip."
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
                clip_cutter_3.name = "Opposite Clip."
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
                value=(radians(90 + dimensions['C'])),
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
    """Generate vertex groups for a triangular core.

    Args:
        obj (bpy.types.Object): Floor core
        dim (dict): triangle specific dimensions
        height (float): Core Height
        base_height (float): Base Height
        native_subdivisions (float): subdivisions per side
    """
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


def create_plain_triangular_floor_cores(base, tile_props):
    """Create preview and displacement cores.

    Args:
        base (bpy.types.Object): tile base
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_floor_core(tile_props)
    textured_vertex_groups = ['Top']
    preview_core, displacement_core = create_displacement_core(
        base,
        preview_core,
        tile_props,
        textured_vertex_groups)
    displacement_core.hide_viewport = True
    return preview_core


def spawn_floor_core(tile_props):
    """Spawn the core (top part) of a floor tile.

    Args:
        tile_props (bpy.types.PropertyGroup.mt_tile_props): tile properties

    Returns:
        bpy.types.Object: tile core
    """
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
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core
