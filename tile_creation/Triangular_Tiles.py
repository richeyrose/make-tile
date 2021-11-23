import os
from math import radians, cos, sqrt, modf
import bpy
import bmesh
from mathutils import Vector
from bpy.types import Panel, Operator

from bpy.props import (
    EnumProperty,
    FloatProperty,
    StringProperty)
from mathutils import Matrix

from .. utils.registration import get_prefs

from ..lib.bmturtle.scripts import (
    draw_tri_prism,
    draw_tri_floor_core,
    draw_tri_slot_cutter)
from ..lib.bmturtle.helpers import (
    bm_select_all,
    bmesh_array,
    extrude_translate)

from .. lib.utils.collections import (
    add_object_to_collection)

from .. lib.utils.utils import mode

from .create_tile import (
    convert_to_displacement_core,
    spawn_empty_base,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    add_subsurf_modifier)

'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


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

        if scene_props.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(scene_props, 'base_socket_type')

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

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Triangular_Floor_Tile(Operator, MT_Tile_Generator):
    """Operator. Create a Triangular Floor Tile."""

    bl_idname = "object.make_triangular_floor"
    bl_label = "Triangle Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "TRIANGULAR_FLOOR"

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

    # @profile
    def exec(self, context):
        base_blueprint = self.base_blueprint
        core_blueprint = self.main_part_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint == 'NONE':
            base = spawn_empty_base(tile_props)
        elif base_blueprint == 'OPENLOCK':
            base = spawn_openlock_base(self, tile_props)
        elif base_blueprint == 'PLAIN':
            base = spawn_plain_base(tile_props)

        if core_blueprint == 'NONE':
            core = None
        else:
            core = create_plain_triangular_floor_cores(base, tile_props)
        self.finalise_tile(context, base, core)

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}
        self.exec(context)
        # profile.dump_stats(splitext(__file__)[0] + '.prof')

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

        if self.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(self, 'base_socket_type')

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

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


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

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(self, tile_props):
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

    clip_cutters = spawn_openlock_base_clip_cutters(
        self, dimensions, tile_props)

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


# @profile
def spawn_openlock_base_clip_cutters(self, dimensions, tile_props):
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

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor_orig_rot = cursor.rotation_euler.copy()

    if a or b or c >= 2:
        preferences = get_prefs()
        cutter_file = self.get_base_socket_filename()
        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes",
            "booleans",
            cutter_file)

        cutters = []
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'openlock.wall.base.cutter.clip.001',
                'openlock.wall.base.cutter.clip.cap.start.001',
                'openlock.wall.base.cutter.clip.cap.end.001']

        cutter = data_to.objects[0]
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        # for cutters the number of cutters and start and end location has to take into account
        # the angles of the triangle in order to prevent overlaps between cutters
        # and issues with booleans

        # b cutter
        if b >= 2:
            me = cutter.data.copy()
            b_cutter = bpy.data.objects.new("Leg 1 Cutter", me)
            bm = bmesh.new()
            bm.from_mesh(me)
            add_object_to_collection(b_cutter, tile_props.tile_name)
            if A >= 90:
                if C >= 90:
                    bm = bmesh_array(
                        source_obj=cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=b - 1)
                else:
                    bm = bmesh_array(
                        source_obj=cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=b - 1.5)
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(0.5, 0.25, 0),
                    space=b_cutter.matrix_world)

            elif A < 90:
                if C >= 90:
                    bm = bmesh_array(
                        source_obj=cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=b - 1.5)
                else:
                    bm = bmesh_array(
                        source_obj=cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=b - 2)
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(0.5, 0.25, 0),
                    space=b_cutter.matrix_world)

            bmesh.ops.rotate(
                bm,
                cent=loc_A,
                verts=bm.verts,
                matrix=Matrix.Rotation(radians(A - 90) * -1, 3, 'Z'),
                space=b_cutter.matrix_world
            )

            bm.to_mesh(me)
            bm.free()
            cutters.append(b_cutter)

        if c >= 2:
            me = cutter.data.copy()
            c_cutter = bpy.data.objects.new("Leg 2 Cutter", me)
            bm = bmesh.new()
            bm.from_mesh(me)
            add_object_to_collection(c_cutter, tile_props.tile_name)

            if B >= 90:
                if A >= 90:
                    bmesh_array(
                        source_obj=c_cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=c - 1)
                else:
                    bmesh_array(
                        source_obj=c_cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=c - 1.5)
                bmesh.ops.rotate(
                    bm,
                    cent=loc_A,
                    verts=bm.verts,
                    matrix=Matrix.Rotation(radians(-90), 3, 'Z'),
                    space=c_cutter.matrix_world)
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(0.25, c - 1, 0.0001),
                    space=c_cutter.matrix_world)
            elif b < 90:
                if A >= 90:
                    bmesh_array(
                        source_obj=c_cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=c - 1.5)
                else:
                    bmesh_array(
                        source_obj=c_cutter,
                        source_bm=bm,
                        start_cap=cutter_start_cap,
                        end_cap=cutter_end_cap,
                        relative_offset_displace=(1, 0, 0),
                        fit_type='FIT_LENGTH',
                        fit_length=c - 2)

                bmesh.ops.rotate(
                    bm,
                    cent=loc_A,
                    verts=bm.verts,
                    matrix=Matrix.Rotation(radians(-90), 3, 'Z'),
                    space=c_cutter.matrix_world)

                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(0.25, c - 1, 0.0001),
                    space=c_cutter.matrix_world)
            bm.to_mesh(me)
            bm.free()
            cutters.append(c_cutter)

        # TODO Simplify this now we only generate socket for isosceles triangles.
        if A == 90 and b == c and a >= 2:
            me = cutter.data.copy()
            a_cutter = bpy.data.objects.new("Leg 3 Cutter", me)
            bm = bmesh.new()
            bm.from_mesh(me)
            add_object_to_collection(a_cutter, tile_props.tile_name)
            turtle = bpy.context.scene.cursor
            turtle.location = loc_C
            turtle.rotation_euler = (0, 0, 0)
            bm.select_mode = {'VERT'}
            bm_select_all(bm)
            dims = cutter.dimensions.copy() + cutter_end_cap.dimensions.copy() + cutter_start_cap.dimensions.copy()
            offset = Vector((1, 0, 0)) * Vector(dims)

            bm = bmesh_array(
                source_obj=a_cutter,
                source_bm=bm,
                start_cap=cutter_start_cap,
                end_cap=cutter_end_cap,
                relative_offset_displace=(1, 0, 0),
                fit_length=(a - 2.5),
                fit_type='FIT_LENGTH')
                
            count = modf((a - 2.5) / offset[0])[1]
            bm.select_mode = {'VERT'}
            bm_select_all(bm)
            turtle.rotation_euler = (0, 0, -radians(A))
            extrude_translate(
                bm, (0, b, 0), del_original=False, extrude=False)
            turtle.rotation_euler = (0, 0, 0)
            extrude_translate(bm, (1, 0.25, 0.0002), extrude=False)
            bmesh.ops.rotate(
                bm,
                verts=bm.verts,
                cent=loc_C,
                matrix=Matrix.Rotation(radians(-90 - B) * -1, 3, 'Z'),
                space=a_cutter.matrix_world)

            caps = 0.083333
            turtle.rotation_euler = (0, 0, radians(C))
            extrude_translate(bm, (0, (caps * (count + 1)), 0),
                                del_original=False, extrude=False)

            bm.to_mesh(me)
            bm.free()
            cutters.append(a_cutter)
        bpy.data.objects.remove(cutter)
        bpy.data.objects.remove(cutter_start_cap)
        bpy.data.objects.remove(cutter_end_cap)

        cursor.location = cursor_orig_loc
        cursor.rotation_euler = cursor_orig_rot
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
    core = spawn_floor_core(tile_props)
    textured_vertex_groups = ['Top']
    material = tile_props.floor_material
    subsurf = add_subsurf_modifier(core)
    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    return core


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

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = core

    return core
