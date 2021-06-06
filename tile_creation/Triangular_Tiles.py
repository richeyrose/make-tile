import os
from math import radians, cos, sqrt
import bpy
from bpy.types import Panel, Operator

from bpy.props import (
    EnumProperty,
    FloatProperty,
    StringProperty)

from .. utils.registration import get_prefs

from ..lib.bmturtle.scripts import (
    draw_tri_prism,
    draw_tri_floor_core,
    draw_tri_slot_cutter)

from .. lib.utils.collections import (
    add_object_to_collection)

from .. lib.utils.utils import mode, get_all_subclasses

from .. lib.utils.selection import select

from .create_tile import (
    convert_to_displacement_core,
    spawn_empty_base,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums)

from ..properties.properties import (
    create_base_blueprint_enums,
    create_main_part_blueprint_enums)


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
        layout.prop(scene_props, 'main_part_blueprint', text="Main")

        layout.label(text="Material")
        layout.prop(scene_props, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(scene_props, 'tile_z', text='Tile Height')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

        layout.label(text="Sync Proportions")
        layout.prop(scene_props, 'z_proportionate_scale')

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text='Base Height')

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Triangular_Floor_Tile(Operator, MT_Tile_Generator):
    """Operator. Create a Triangular Floor Tile."""

    bl_idname = "object.make_triangular_floor"
    bl_label = "Triangle Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "TRIANGULAR_FLOOR"

    def update_base_blueprint_enums(self, context):
        if not self.invoked:
            if self.base_blueprint in ("OPENLOCK", "PLAIN"):
                self.base_y = 0.5
                self.base_z = 0.2755
            else:
                self.base_y = self.tile_y
                self.base_z = 0.0

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        name="Wall")

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_blueprint_enums,
        name="Base"
    )

    angle: FloatProperty(
        name="Base Angle",
        default=90,
        step=500,
        precision=0
    )

    leg_1_len: FloatProperty(
        name="Leg 1 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    leg_2_len: FloatProperty(
        name="Leg 2 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}

        base_blueprint = self.base_blueprint
        core_blueprint = self.main_part_blueprint
        base_type = 'TRIANGULAR_BASE'
        core_type = 'TRIANGULAR_FLOOR_CORE'
        subclasses = get_all_subclasses(MT_Tile_Generator)

        kwargs = {"tile_name": self.tile_name}
        base = spawn_prefab(context, subclasses, base_blueprint, base_type, **kwargs)

        kwargs["base_name"] = base.name
        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_prefab(context, subclasses, core_blueprint, core_type, **kwargs)

        self.finalise_tile(context, base, preview_core)

        return {'FINISHED'}

    def init(self, context):
        super().init(context)
        tile_collection = bpy.data.collections[self.tile_name]
        tile_props = tile_collection.mt_tile_props
        tile_props.collection_type = "TILE"
        tile_props.tile_size = (self.tile_x, self.tile_y, self.tile_z)
        tile_props.base_size = (self.base_x, self.base_y, self.base_z)

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        layout.label(text="Blueprints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint', text="Main")

        layout.label(text="Material")
        layout.prop(self, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(self, 'tile_z', text='Tile Height')
        layout.prop(self, 'leg_1_len', text='Leg 1 Length')
        layout.prop(self, 'leg_2_len', text='Leg 2 Length')
        layout.prop(self, 'angle', text='Angle')

        layout.label(text="Sync Proportions")
        layout.prop(self, 'z_proportionate_scale')

        layout.label(text="Base Properties")
        layout.prop(self, 'base_z', text='Base Height')


class MT_OT_Make_Openlock_Triangular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK triangular base."""

    bl_idname = "object.make_openlock_triangular_base"
    bl_label = "Triangular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "TRIANGULAR_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
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
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain triangular core."""

    bl_idname = "object.make_plain_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "TRIANGULAR_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]
        create_plain_triangular_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock triangular floor core."""

    bl_idname = "object.make_openlock_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "TRIANGULAR_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]
        create_plain_triangular_floor_cores(base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Triangular_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty triangular floor core."""

    bl_idname = "object.make_empty_triangular_floor_core"
    bl_label = "Triangular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "TRIANGULAR_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def spawn_plain_base(tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    tile_name = tile_props.tile_name
    base = draw_tri_prism(dimensions={
        'b': tile_props.leg_1_len,
        'c': tile_props.leg_2_len,
        'A': tile_props.angle,
        'height': tile_props.base_size[2]
    })

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
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    dimensions = {
        'b': tile_props.leg_1_len,
        'c': tile_props.leg_2_len,
        'A': tile_props.angle,
        'height': tile_props.base_size[2]}
    tile_name = tile_props.tile_name

    base, dimensions = draw_tri_prism(dimensions, True)

    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base],
        'selected_editable_objects': [base]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    clip_cutters = spawn_openlock_base_clip_cutters(dimensions, tile_props)

    for clip_cutter in clip_cutters:
        set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    slot_cutter = draw_tri_slot_cutter(dimensions)
    set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

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
    #      B
    #      /\
    #   c /  \ a
    #    /    \
    #   /______\
    #  A    b    C

    # b = Leg 1
    # c = Leg 2

    a = dimensions['a']
    b = dimensions['b']
    c = dimensions['c']
    A = dimensions['A']
    B = dimensions['B']
    C = dimensions['C']
    loc_A = dimensions['loc_A']
    loc_B = dimensions['loc_B']
    loc_C = dimensions['loc_C']

    if a or b or c >= 2:
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

        b_cutter = data_to.objects[0]

        b_cutter.name = "Leg 1 Clip."
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        # cutter_start_cap.hide_set(True)
        # cutter_end_cap.hide_set(True)
        cutter_start_cap.hide_viewport = True
        cutter_end_cap.hide_viewport = True

        array_mod = b_cutter.modifiers.new('Array', 'ARRAY')
        array_mod.start_cap = cutter_start_cap
        array_mod.end_cap = cutter_end_cap
        array_mod.use_merge_vertices = True

        array_mod.fit_type = 'FIT_LENGTH'

        # for cutters the number of cutters and start and end location has to take into account
        # the angles of the triangle in order to prevent overlaps between cutters
        # and issues with booleans

        # b cutter
        if b >= 2:
            if A >= 90:
                b_cutter.location = (
                    loc_A[0] + 0.5,
                    loc_A[1] + 0.25,
                    loc_A[2])
                if C >= 90:
                    array_mod.fit_length = b - 1
                else:
                    array_mod.fit_length = b - 1.5

            elif A < 90:
                b_cutter.location = (
                    loc_A[0] + 1,
                    loc_A[1] + 0.25,
                    loc_A[2])
                if C >= 90:
                    array_mod.fit_length = b - 1.5
                else:
                    array_mod.fit_length = b - 2

            ctx = {
                'object': b_cutter,
                'active_object': b_cutter,
                'selected_objects': [b_cutter],
                'selected_editable_objects': [b_cutter]}

            bpy.ops.transform.rotate(
                ctx,
                value=radians(A - 90) * 1,
                orient_axis='Z',
                orient_type='GLOBAL',
                center_override=loc_A)

            c_cutter = b_cutter.copy()
            c_cutter.name = "Leg 2 Clip"
            add_object_to_collection(c_cutter, tile_props.tile_name)
            cutters.append(b_cutter)
        else:
            c_cutter = b_cutter

        if c >= 2:
            array_mod = c_cutter.modifiers['Array']
            c_cutter.rotation_euler = (0, 0, radians(-90))

            if B >= 90:
                c_cutter.location = (
                    loc_B[0] + 0.25,
                    loc_B[1] - 0.5,
                    loc_B[2] + 0.0001)
                if A >= 90:
                    array_mod.fit_length = c - 1
                else:
                    array_mod.fit_length = c - 1.5

            elif B < 90:
                c_cutter.location = (
                    loc_B[0] + 0.25,
                    loc_B[1] - 1,
                    loc_B[2] + 0.0001)
                if A >= 90:
                    array_mod.fit_length = c - 1.5
                else:
                    array_mod.fit_length = c - 2
            cutters.append(c_cutter)

            if a >= 2:
                a_cutter = c_cutter.copy()
                a_cutter.name = "Opposite Clip."
                add_object_to_collection(a_cutter, tile_props.tile_name)
            else:
                bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)
                return cutters
        else:
            a_cutter = c_cutter

        # clip cutter 3
        if a >= 2:
            a_cutter.rotation_euler = (0, 0, 0)
            array_mod = a_cutter.modifiers['Array']

            if C >= 90:
                a_cutter.location = (
                    loc_C[0] + 0.5,
                    loc_C[1] + 0.25,
                    loc_C[2] + 0.0002)
                if B >= 90:
                    array_mod.fit_length = a - 1
                else:
                    array_mod.fit_length = a - 1.5

            elif C < 90:
                a_cutter.location = (
                    loc_C[0] + 1,
                    loc_C[1] + 0.25,
                    loc_C[2] + 0.0002)
                if B >= 90:
                    array_mod.fit_length = a - 1.5
                else:
                    array_mod.fit_length = a - 2
            ctx = {
                'object': a_cutter,
                'active_object': a_cutter,
                'selected_objects': [a_cutter],
                'selected_editable_objects': [a_cutter]}

            bpy.ops.transform.rotate(
                ctx,
                value=radians(-90 - B) * 1,
                orient_axis='Z',
                orient_type='GLOBAL',
                center_override=loc_C)

            cutters.append(a_cutter)

            bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)
        return cutters
    else:
        return None


def create_plain_triangular_floor_cores(base, tile_props):
    """Create preview and displacement cores.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    preview_core = spawn_floor_core(tile_props)
    textured_vertex_groups = ['Top']
    material=tile_props.floor_material
    convert_to_displacement_core(
        preview_core,
        textured_vertex_groups,
        material)

    return preview_core


def spawn_floor_core(tile_props):
    """Spawn the core (top part) of a floor tile.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile core
    """
    tile_name = tile_props.tile_name
    b = tile_props.leg_1_len
    c = tile_props.leg_2_len
    A = tile_props.angle
    hyp = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    native_subdivisions = get_subdivs(
        tile_props.subdivision_density,
        [hyp, tile_props.tile_size[2] - tile_props.base_size[2]])
    core = draw_tri_floor_core(
        dimensions={
            'b': b,
            'c': c,
            'A': A,
            'height': tile_props.tile_size[2] - tile_props.base_size[2]
        },
        subdivs=native_subdivisions
    )
    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_name)

    mode('OBJECT')

    core.location[2] = core.location[2] + tile_props.base_size[2]

    #TODO Factor the below out as duplicated in each tile generator
    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core],
        'selected_editable_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core
