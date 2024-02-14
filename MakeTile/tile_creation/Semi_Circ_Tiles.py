import os
from math import (
    radians,
    pi)
from mathutils import Matrix

from mathutils.geometry import intersect_line_line
import bpy
import bmesh
from bpy.types import Operator, Panel
from bpy.props import (
    EnumProperty,
    FloatProperty,
    StringProperty)

from . create_tile import (
    convert_to_displacement_core,
    spawn_empty_base,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    add_subsurf_modifier)

from .. utils.registration import get_prefs
from .. lib.utils.selection import (
    activate)
from .. lib.utils.utils import (
    mode,
    distance_between_two_points,
    calc_tri)
from .. lib.utils.collections import (
    add_object_to_collection)
from ..lib.bmturtle.helpers import (
    bm_select_all,
    bmesh_array,
    select_verts_in_bounds,
    assign_verts_to_group,
    calculate_corner_wall_triangles)
from ..lib.bmturtle.commands import (
    create_turtle,
    home,
    finalise_turtle,
    add_vert,
    fd,
    pu,
    pd,
    rt,
    lt,
    up,
    dn,
    arc)

'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


class MT_PT_Semi_Circ_Floor_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Semi_Circ_Floor_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "SEMI_CIRC_FLOOR"
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
            layout.prop(scene_props, 'generate_suppports')

        layout.label(text="Material")
        layout.prop(scene_props, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(scene_props, 'tile_z', text="Height")
        layout.prop(scene_props, 'base_radius', text="Radius")
        layout.prop(scene_props, 'semi_circ_angle', text="Angle")
        layout.prop(scene_props, 'curve_type', text="Curve Type")

        layout.label(text="Sync Proportions")
        layout.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Semi_Circ_Floor_Tile(Operator, MT_Tile_Generator):
    """Create a Semi Circular Floor Tile."""

    bl_idname = "object.make_semi_circ_floor"
    bl_label = "Semi Circular Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "SEMI_CIRC_FLOOR"

    curve_type: EnumProperty(
        items=[
            ("POS", "Positive", ""),
            ("NEG", "Negative", "")],
        name="Curve type",
        default="POS",
        description="Whether the tile has a positive or negative curvature"
    )

    base_radius: FloatProperty(
        name="Base inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0,
    )

    semi_circ_angle: FloatProperty(
        name="Angle",
        default=90,
        step=500,
        precision=0,
        max=179.999,
        min=45
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
            base = spawn_plain_base(self, tile_props)

        if core_blueprint == 'NONE':
            preview_core = None
        else:
            preview_core = spawn_plain_floor_cores(self, tile_props)

        self.finalise_tile(context, base, preview_core)
        # profile.dump_stats(splitext(__file__)[0] + '.prof')
        return {'FINISHED'}

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}

        return self.exec(context)

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

        layout.label(text="Bluperints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint', text="Main")

        if self.base_blueprint not in ('PLAIN', 'NONE'):
            layout.prop(self, 'base_socket_type')
            layout.prop(scene_props, 'generate_suppports')

        layout.label(text="Material")
        layout.prop(self, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(self, 'tile_z', text="Height")
        layout.prop(self, 'base_radius', text="Radius")
        layout.prop(self, 'semi_circ_angle', text="Angle")
        layout.prop(self, 'curve_type', text="Curve Type")

        layout.label(text="Sync Proportions")
        layout.prop(self, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(self, 'base_z', text="Height")

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


class MT_OT_Make_Openlock_Semi_Circ_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK semi circular base."""

    bl_idname = "object.make_openlock_semi_circ_base"
    bl_label = "OpenLOCK Semi-Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_openlock_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Semi_Circ_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain semi circular base."""

    bl_idname = "object.make_plain_semi_circ_base"
    bl_label = "Plain Semi Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Semi_Circular_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty semi circular base."""

    bl_idname = "object.make_empty_semi_circ_base"
    bl_label = "Empty Semi Circular Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "SEMI_CIRC_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain semi circular floor core."""

    bl_idname = "object.make_plain_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "SEMI_CIRC_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock semi circular floor core."""

    bl_idname = "object.make_openlock_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "SEMI_CIRC_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Semi_Circ_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty semi circular floor core."""

    bl_idname = "object.make_empty_semi_circ_floor_core"
    bl_label = "Semi Circular Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "SEMI_CIRC_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def spawn_plain_base(self, tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    angle = tile_props.semi_circ_angle
    radius = tile_props.base_radius
    subdivs = {
        'arc': (angle / 360) * (2 * pi) * radius}
    subdivs = get_subdivs(tile_props.subdivision_density, subdivs)

    dimensions = {
        'height': tile_props.base_size[2],
        'angle': angle,
        'radius': radius}

    curve_type = tile_props.curve_type

    if curve_type == 'POS':
        base = draw_pos_curved_semi_circ_base(dimensions, subdivs)
    else:
        base = draw_neg_curved_semi_circ_base(dimensions, subdivs)

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base(self, tile_props):
    """Spawn OpenLOCK base into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base
    """
    curve_type = tile_props.curve_type

    angle = tile_props.semi_circ_angle
    radius = tile_props.base_radius

    dimensions = {
        'height': tile_props.base_size[2],
        'angle': angle,
        'radius': radius,
        'outer_w': 0.236,
        'slot_w': 0.181,
        'slot_h': 0.24}

    subdivs = {
        'arc': (angle / 360) * (2 * pi) * radius}
    subdivs = get_subdivs(tile_props.subdivision_density, subdivs)

    base = spawn_plain_base(self, tile_props)

    base.mt_object_props.geometry_type = 'BASE'

    base.name = tile_props.tile_name + '.base'
    props = base.mt_object_props
    props.is_mt_object = True
    props.tile_name = tile_props.tile_name
    props.geometry_type = 'BASE'

    slot_cutter = None
    if curve_type == 'POS':
        slot_cutter = draw_pos_curved_slot_cutter(dimensions, subdivs)
    else:
        if dimensions['radius'] >= 2:
            slot_cutter = draw_neg_curved_slot_cutter(dimensions)

    if slot_cutter:
        slot_cutter.name = 'Slot.cutter.' + base.name
        set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(slot_cutter, base, 'DIFFERENCE')

    cutters = create_openlock_base_clip_cutters(self, tile_props)

    for clip_cutter in cutters:
        set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(clip_cutter, base, 'DIFFERENCE')

    bpy.context.view_layer.objects.active = base

    return base


def spawn_plain_floor_cores(self, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    core = spawn_core(self, tile_props)
    textured_vertex_groups = ['Top']
    material = tile_props.floor_material
    subsurf = add_subsurf_modifier(core)

    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    return core


def spawn_core(self, tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    base_size = tile_props.base_size
    curve_type = tile_props.curve_type

    radius = tile_props.base_radius
    angle = tile_props.semi_circ_angle
    height = tile_props.tile_size[2] - tile_props.base_size[2]
    dimensions = {
        'radius': radius,
        'angle': angle,
        'height': height}

    subdivs = {
        'sides': radius,
        'arc': (angle / 360) * (2 * pi) * radius,
        'z': height}
    subdivs = get_subdivs(tile_props.subdivision_density, subdivs)

    # In order for grid fill to work the sum of verts on the sides needs to be even
    vert_sum = subdivs['arc'] + subdivs['sides']

    if vert_sum % 2 > 0:
        subdivs['arc'] = subdivs['arc'] - 1

    if curve_type == 'POS':
        core = draw_pos_curved_semi_circ_core(dimensions, subdivs)
    else:
        core = draw_neg_curved_semi_circ_core(dimensions, subdivs)

    core.location[2] = core.location[2] + base_size[2]
    core.name = tile_props.tile_name + '.core'

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name
    return core


def create_openlock_base_clip_cutters(self, tile_props):
    """Generate base clip cutters for semi circular tiles.

    Args:
        tile_props (bpy.types.MT_Tile_Properties): tile properties

    Returns:
        list[bpy.types.Object]: Base cutters
    """
    mode('OBJECT')

    cursor = bpy.context.scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor.location = (0, 0, 0)
    radius = tile_props.base_radius
    angle = tile_props.semi_circ_angle
    curve_type = tile_props.curve_type
    cutters = []

    preferences = get_prefs()
    cutter_file = self.get_base_socket_filename()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        cutter_file)

    if curve_type == 'NEG':
        radius = radius / 2

    if radius >= 1:
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'openlock.wall.base.cutter.clip.001',
                'openlock.wall.base.cutter.clip.cap.start.001',
                'openlock.wall.base.cutter.clip.cap.end.001']
        '''
        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)
        '''
        cutter = data_to.objects[0]
        cutter_start_cap = data_to.objects[1]
        cutter_end_cap = data_to.objects[2]

        clip_cutter_1 = bpy.data.objects.new(
            "Clip Cutter 1", cutter.data.copy())
        add_object_to_collection(clip_cutter_1, tile_props.tile_name)

        me = clip_cutter_1.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)

        if angle >= 90:
            bm = bmesh_array(
                source_obj=clip_cutter_1,
                source_bm=bm,
                start_cap=cutter_start_cap,
                end_cap=cutter_end_cap,
                relative_offset_displace=(1, 0, 0),
                fit_type='FIT_LENGTH',
                fit_length=radius - 1)

            bmesh.ops.translate(
                bm,
                verts=bm.verts,
                vec=(0.5, 0.25, 0),
                space=clip_cutter_1.matrix_world)

        else:
            bm = bmesh_array(
                source_obj=clip_cutter_1,
                source_bm=bm,
                start_cap=cutter_start_cap,
                end_cap=cutter_end_cap,
                relative_offset_displace=(1, 0, 0),
                fit_type='FIT_LENGTH',
                fit_length=radius - 1.5)

            bmesh.ops.translate(
                bm,
                verts=bm.verts,
                vec=(1, 0.25, 0),
                space=clip_cutter_1.matrix_world)

        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=cursor_orig_loc,
            matrix=Matrix.Rotation(radians(angle - 90) * -1, 3, 'Z'),
            space=clip_cutter_1.matrix_world)

        bm.to_mesh(clip_cutter_1.data)
        bm.free()

        cutters.append(clip_cutter_1)

        clip_cutter_2 = bpy.data.objects.new(
            "Clip Cutter 2", cutter.data.copy())
        add_object_to_collection(clip_cutter_2, tile_props.tile_name)

        me = clip_cutter_2.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)

        if angle >= 90:
            bm = bmesh_array(
                source_obj=clip_cutter_2,
                source_bm=bm,
                start_cap=cutter_start_cap,
                end_cap=cutter_end_cap,
                relative_offset_displace=(1, 0, 0),
                fit_type='FIT_LENGTH',
                fit_length=radius - 1)

        else:
            bm = bmesh_array(
                source_obj=clip_cutter_2,
                source_bm=bm,
                start_cap=cutter_start_cap,
                end_cap=cutter_end_cap,
                relative_offset_displace=(1, 0, 0),
                fit_type='FIT_LENGTH',
                fit_length=radius - 1.5)

        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=cursor_orig_loc,
            matrix=Matrix.Rotation(radians(270), 3, 'Z'),
            space=clip_cutter_1.matrix_world)

        bmesh.ops.translate(
            bm,
            verts=bm.verts,
            vec=(0.25, radius - 0.5, 0),
            space=clip_cutter_2.matrix_world)

        bm.to_mesh(clip_cutter_2.data)
        bm.free()
        cutters.append(clip_cutter_2)

    bpy.data.objects.remove(cutter)
    bpy.data.objects.remove(cutter_end_cap)
    bpy.data.objects.remove(cutter_start_cap)

    if tile_props.curve_type == 'POS':
        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = ['openlock.wall.base.cutter.clip_single']
        cutter = data_to.objects[0]

        clip_cutter_3 = bpy.data.objects.new(
            "Clip Cutter 3", cutter.data.copy())
        add_object_to_collection(clip_cutter_3, tile_props.tile_name)

        me = clip_cutter_3.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)

        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=clip_cutter_3.location,
            matrix=Matrix.Rotation(radians(180), 3, 'Z'),
            space=clip_cutter_3.matrix_world)
        '''

        clip_cutter_3.rotation_euler = (0, 0, radians(180))
        clip_cutter_3.location[1] = cursor_orig_loc[1] + radius - 0.25
        '''
        bmesh.ops.translate(
            bm,
            verts=bm.verts,
            vec=(0, radius - 0.25, 0),
            space=clip_cutter_3.matrix_world)

        bmesh.ops.rotate(
            bm,
            cent=cursor_orig_loc,
            verts=bm.verts,
            matrix=Matrix.Rotation(radians(angle / 2) * -1, 3, 'Z'),
            space=clip_cutter_3.matrix_world)

        bm.to_mesh(clip_cutter_3.data)
        bm.free()
        cutters.append(clip_cutter_3)
        bpy.data.objects.remove(cutter)

    for cutter in cutters:
        props = cutter.mt_object_props
        props.is_mt_object = True
        props.tile_name = tile_props.tile_name

    return cutters


def draw_pos_curved_semi_circ_base(dimensions, subdivs):
    """Return a positively curved semi circular base.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: base
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    bm, obj = create_turtle('base')
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)
    fd(bm, radius)
    pu(bm)
    home(obj)
    pd(bm)

    # we only draw part of the arc and then join the end to the final side later
    # we do this because there's always a difference in the location of the final
    # vert  of the arc and the final vert of the side it needs to connect to so
    # merge by distance doesn't work.
    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)
    arc(bm, radius, part_angle, subdivs['arc'] - 1)
    pd(bm)
    add_vert(bm)
    rt(angle)
    fd(bm, radius)
    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)

    # join final vert of arc with side
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    bmesh.ops.triangle_fill(bm, use_beauty=True,
                            use_dissolve=False, edges=bm.edges)
    pd(bm)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)
    pu(bm)
    home(obj)

    finalise_turtle(bm, obj)
    return obj


def draw_neg_curved_semi_circ_base(dimensions, subdivs):
    """Return a negatively curved semi circular base.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: base
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    # calculate a triangle that is the mirror of the one formed by legs b an c
    triangle = calc_tri(angle, radius, radius)

    bm, obj = create_turtle('base')
    verts = bm.verts
    bm.select_mode = {'VERT'}
    pd(bm)
    add_vert(bm)

    fd(bm, radius)
    pu(bm)
    home(obj)
    pd(bm)
    rt(angle)
    add_vert(bm)
    fd(bm, radius)
    pu(bm)
    lt(180 - triangle['C'] * 2)
    fd(bm, radius)
    lt(180)

    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)
    pu(bm)
    home(obj)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.01)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    bmesh.ops.triangle_fill(bm, use_beauty=True,
                            use_dissolve=False, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, height, False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)

    return obj


def draw_pos_curved_semi_circ_core(dimensions, subdivs, margin=0.001):
    """Return a positively curved semi circular core.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{
            sides: float,
            arc: float}): subdivisions
        margin (float): margin between texturewd and blank area

    Returns:
        bpy.type.Object: core
    """
    #   B
    #   |\
    # c |   \ a
    #   |      \
    #   |________ \
    #  A    b    C
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    vert_groups = [
        'Side a',
        'Side b',
        'Side c',
        'Top',
        'Bottom']

    vert_locs = {
        'Side a': [],
        'Side b': [],
        'Side c': [],
        'Top': [],
        'Bottom': []}

    bm, obj = create_turtle('core', vert_groups)
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)

    verts.ensure_lookup_table()
    vert_locs['Side c'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side c'].append(verts[-1].co.copy())
        i += 1

    pu(bm)
    home(obj)
    pd(bm)

    verts.ensure_lookup_table()
    start_index = verts[-1].index + 1

    # only draw n-1 segments of arc as we will join arc and side together later
    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)

    verts.ensure_lookup_table()
    i = start_index
    while i <= verts[-1].index:
        vert_locs['Side a'].append(verts[i].co.copy())
        i += 1

    pd(bm)
    add_vert(bm)
    rt(angle)

    verts.ensure_lookup_table()
    vert_locs['Side b'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side b'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because or error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=margin / 2)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)

    # bmesh.ops.grid_fill doesn't work as well as bpy.ops.grid_fill so we use that instead despite
    # it being slower and requiring us to rebuild our bmesh

    bm_select_all(bm)
    bm.select_flush(True)
    mesh = obj.data
    bm.to_mesh(mesh)
    bm.free()

    activate(obj.name)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.fill_grid(span=subdivs['sides'])
    bpy.ops.object.editmode_toggle()

    bm = bmesh.new()
    bm.from_mesh(mesh)

    pd(bm)
    verts = bm.verts
    bottom_verts = [v for v in verts]

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, height, False)

    selected_faces = [f for f in bm.faces if f.select]

    bmesh.ops.inset_region(
        bm,
        faces=selected_faces,
        thickness=margin,
        use_boundary=True,
        use_even_offset=True)

    verts.layers.deform.verify()
    deform_groups = verts.layers.deform.active

    side_b_verts = []
    for loc in vert_locs['Side b']:
        side_b_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    side_c_verts = select_verts_in_bounds(
        lbound=obj.location,
        ubound=(obj.location[0], obj.location[1] +
                radius, obj.location[2] + height),
        buffer=margin / 2,
        bm=bm)

    side_a_verts = []
    for loc in vert_locs['Side a']:
        side_a_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    # verts not to include in top
    vert_list = bottom_verts + side_a_verts + side_b_verts + side_c_verts

    # assign verts to groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')
    assign_verts_to_group(side_a_verts, obj, deform_groups, 'Side a')
    assign_verts_to_group(side_c_verts, obj, deform_groups, 'Side c')
    assign_verts_to_group(side_b_verts, obj, deform_groups, 'Side b')
    assign_verts_to_group(
        [v for v in bm.verts if v not in vert_list],
        obj,
        deform_groups,
        'Top')

    finalise_turtle(bm, obj)
    return obj


def draw_neg_curved_semi_circ_core(dimensions, subdivs, margin=0.001):
    """Return a negatively curved semi circular core.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{
            sides: float,
            arc: float}): subdivisions
        margin (float): margin between texturewd and blank area

    Returns:
        bpy.type.Object: core
    """
    #   B
    #   |\
    # c |   \ a
    #   |      \
    #   |________ \
    #  A    b    C
    radius = dimensions['radius']
    angle = dimensions['angle']
    height = dimensions['height']

    vert_groups = [
        'Side a',
        'Side b',
        'Side c',
        'Top',
        'Bottom']

    vert_locs = {
        'Side a': [],
        'Side b': [],
        'Side c': [],
        'Top': [],
        'Bottom': []}

    # calculate a triangle that is the mirror of the one formed by legs b an c
    triangle = calc_tri(angle, radius, radius)

    bm, obj = create_turtle('core', vert_groups)
    verts = bm.verts

    bm.select_mode = {'VERT'}
    add_vert(bm)

    verts.ensure_lookup_table()
    vert_locs['Side c'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side c'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because of margin of error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    home(obj)
    pd(bm)

    rt(angle)
    add_vert(bm)
    verts.ensure_lookup_table()
    vert_locs['Side b'].append(verts[-1].co.copy())

    i = 0
    while i < subdivs['sides']:
        fd(bm, radius / subdivs['sides'])
        verts.ensure_lookup_table()
        vert_locs['Side b'].append(verts[-1].co.copy())
        i += 1

    # save this vert to side a as well because or error when drawing arc
    vert_locs['Side a'].append(verts[-1].co.copy())

    pu(bm)
    lt(180 - triangle['C'] * 2)
    fd(bm, radius)
    lt(180)

    verts.ensure_lookup_table()
    start_index = bm.verts[-1].index + 1

    part_angle = (angle / subdivs['arc'])
    part_angle = part_angle * (subdivs['arc'] - 1)

    arc(bm, radius, part_angle, subdivs['arc'] - 1)

    verts.ensure_lookup_table()
    i = start_index
    while i <= verts[-1].index:
        vert_locs['Side a'].append(verts[i].co.copy())
        i += 1

    pu(bm)
    home(obj)

    bmesh.ops.remove_doubles(bm, verts=verts, dist=margin / 2)
    bmesh.ops.edgenet_prepare(bm, edges=bm.edges)
    bmesh.ops.triangle_fill(bm, use_beauty=True, edges=bm.edges)
    faces = sorted(bm.faces, key=lambda f: f.calc_area())
    # get edges in this face
    edges = [e for e in faces[-1].edges]
    # subdivide edges in this face  
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    # subdivide the other edges
    # bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bottom_verts = [v for v in bm.verts]

    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, height, False)

    selected_faces = [f for f in bm.faces if f.select]

    bmesh.ops.inset_region(
        bm,
        faces=selected_faces,
        thickness=margin,
        use_boundary=True,
        use_even_offset=False)

    verts.layers.deform.verify()
    deform_groups = verts.layers.deform.active

    side_b_verts = []
    for loc in vert_locs['Side b']:
        side_b_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    side_c_verts = select_verts_in_bounds(
        lbound=obj.location,
        ubound=(obj.location[0], obj.location[1] +
                radius, obj.location[2] + height),
        buffer=margin / 2,
        bm=bm)

    side_a_verts = []
    for loc in vert_locs['Side a']:
        side_a_verts.extend(select_verts_in_bounds(
            lbound=loc,
            ubound=(loc[0], loc[1], loc[2] + height),
            buffer=margin / 2,
            bm=bm))

    # verts not to include in top
    vert_list = bottom_verts + side_a_verts + side_b_verts + side_c_verts

    # assign verts to groups
    assign_verts_to_group(bottom_verts, obj, deform_groups, 'Bottom')
    assign_verts_to_group(side_a_verts, obj, deform_groups, 'Side a')
    assign_verts_to_group(side_c_verts, obj, deform_groups, 'Side c')
    assign_verts_to_group(side_b_verts, obj, deform_groups, 'Side b')
    assign_verts_to_group(
        [v for v in bm.verts if v not in vert_list],
        obj,
        deform_groups,
        'Top')

    finalise_turtle(bm, obj)
    return obj


def draw_pos_curved_slot_cutter(dimensions, subdivs):
    """Return a positively curved base slot cutter.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions
        subdivs (dict{arc: float}): subdivisions

    Returns:
        bpy.type.Object: slot cutter
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    outer_w = dimensions['outer_w']
    slot_w = dimensions['slot_w']
    slot_h = dimensions['slot_h']

    bm, obj = create_turtle('base')
    verts = bm.verts

    bm.select_mode = {'VERT'}
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    pu(bm)

    # get locs of ends of edges inside and parallel to base outer edges
    rt(angle)
    fd(bm, radius / 2)
    lt(90)
    fd(bm, outer_w)
    lt(90)
    v1 = turtle.location.copy()
    fd(bm, 0.01)
    v2 = turtle.location.copy()

    home(obj)
    fd(bm, radius / 2)
    rt(90)
    fd(bm, outer_w)
    rt(90)
    v3 = turtle.location.copy()
    fd(bm, 0.01)
    v4 = turtle.location.copy()

    # get intersection
    intersection = intersect_line_line(v1, v2, v3, v4)
    intersection = (intersection[0] + intersection[1]) / 2
    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)
    dist = distance_between_two_points(origin, intersection)

    new_radius = radius - dist - outer_w

    # draw outer arc
    arc(bm, new_radius, angle, subdivs['arc'] + 1)

    # draw sides
    add_vert(bm)
    pd(bm)
    fd(bm, new_radius)
    pu(bm)
    turtle.location = intersection
    pd(bm)
    verts.ensure_lookup_table()
    verts[-2].select = True
    rt(angle)
    fd(bm, new_radius)
    pu(bm)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)

    # repeat for inner edge of slot cutter
    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)

    # get locs of ends of edges inside and parallel to base outer edges
    rt(angle)
    fd(bm, radius / 2)
    lt(90)
    fd(bm, slot_w)
    lt(90)
    v1 = turtle.location.copy()
    fd(bm, 0.01)
    v2 = turtle.location.copy()

    turtle.location = intersection
    turtle.rotation_euler = (0, 0, 0)
    fd(bm, radius / 2)
    rt(90)
    fd(bm, slot_w)
    rt(90)
    v3 = turtle.location.copy()
    fd(bm, 0.01)
    v4 = turtle.location.copy()

    # get intersection
    intersection_2 = intersect_line_line(v1, v2, v3, v4)
    intersection_2 = (intersection_2[0] + intersection_2[1]) / 2
    turtle.location = intersection_2
    turtle.rotation_euler = (0, 0, 0)
    dist = distance_between_two_points(intersection, intersection_2)

    new_radius = new_radius - dist - slot_w

    # draw outer arc
    arc(bm, new_radius, angle, subdivs['arc'] + 1)
    add_vert(bm)
    pd(bm)
    fd(bm, new_radius)
    pu(bm)
    turtle.location = intersection_2
    pd(bm)
    verts.ensure_lookup_table()
    verts[-2].select = True
    rt(angle)
    fd(bm, new_radius)
    pu(bm)
    bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)
    bmesh.ops.bridge_loops(bm, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    pd(bm)
    up(bm, slot_h + 0.001, False)
    pu(bm)
    home(obj)
    obj.location = (obj.location[0], obj.location[1], obj.location[2] - 0.001)
    finalise_turtle(bm, obj)

    return obj


def draw_neg_curved_slot_cutter(dimensions):
    """Return a negatively curved base slot cutter.

    Args:
        dimensions (dict{
            radius: float,
            angle: float,
            height: float}): dimensions

    Returns:
        bpy.type.Object: slot cutter
    """
    radius = dimensions['radius']
    angle = dimensions['angle']
    outer_w = dimensions['outer_w']
    slot_w = dimensions['slot_w']
    slot_h = dimensions['slot_h'] + 0.001

    triangles_1 = calculate_corner_wall_triangles(
        radius,
        radius,
        outer_w,
        angle)

    x_leg = triangles_1['b_adj'] - outer_w
    y_leg = triangles_1['d_adj'] - outer_w

    triangles_2 = calculate_corner_wall_triangles(
        x_leg,
        y_leg,
        slot_w,
        angle)

    bm, obj = create_turtle('slot_cutter')
    bm.select_mode = {'VERT'}

    turtle = bpy.context.scene.cursor
    # move turtle to start
    orig_rot = turtle.rotation_euler.copy()

    pu(bm)
    dn(bm, 0.001)
    rt(angle)
    fd(bm, triangles_1['a_adj'])
    lt(90)
    fd(bm, outer_w)
    lt(90)
    fd(bm, triangles_1['b_adj'])
    turtle.rotation_euler = orig_rot
    turtle_start_loc = turtle.location.copy()
    pd(bm)

    add_vert(bm)
    rt(angle)
    fd(bm, triangles_2['a_adj'] - (radius / 2))
    lt(90)
    fd(bm, slot_w)
    lt(90)
    fd(bm, triangles_2['b_adj'] - (radius / 2))
    pu(bm)
    home(obj)
    turtle.location = turtle_start_loc
    pd(bm)
    add_vert(bm)
    fd(bm, triangles_2['c_adj'] - (radius / 2))
    rt(90)
    fd(bm, slot_w)
    rt(90)
    fd(bm, triangles_2['d_adj'] - (radius / 2))

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bmesh.ops.triangle_fill(bm, use_beauty=True,
                            use_dissolve=False, edges=bm.edges)
    bm.select_mode = {'FACE'}
    bm_select_all(bm)
    up(bm, slot_h, False)
    pu(bm)
    home(obj)
    finalise_turtle(bm, obj)
    return obj
