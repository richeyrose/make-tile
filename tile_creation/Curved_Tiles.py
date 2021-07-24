import os
from math import radians, pi, modf, degrees
import bpy
import bmesh
from mathutils import Matrix
from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    BoolProperty,
    StringProperty)

from ..lib.utils.collections import (
    add_object_to_collection)

from ..utils.registration import get_prefs

from ..lib.bmturtle.scripts import (
    draw_straight_wall_core,
    draw_rectangular_floor_core,
    draw_curved_cuboid)

from ..lib.bmturtle.helpers import bmesh_array

from ..lib.utils.selection import (
    deselect_all,
    select,
    activate)

from .create_tile import (
    convert_to_displacement_core,
    spawn_empty_base,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    add_subsurf_modifier)
'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


class MT_PT_Curved_Wall_Tile_Panel(Panel):
    """Draw a tile options panel in the UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 1
    bl_idname = "MT_PT_Curved_Wall_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "CURVED_WALL"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props

        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Materials")
        layout.prop(scene_props, 'floor_material')
        layout.prop(scene_props, 'wall_material')

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_z', text="Height")
        layout.prop(scene_props, 'base_radius', text="Radius")
        layout.prop(scene_props, 'degrees_of_arc')
        layout.prop(scene_props, 'base_socket_side', text="Socket Side")
        layout.prop(scene_props, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        if scene_props.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.label(text="Floor Thickness")
            layout.prop(scene_props, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(scene_props, 'wall_position', text="")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'y_proportionate_scale', text="Width")
        row.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text="Width")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_PT_Curved_Floor_Tile_Panel(Panel):
    """Draw a tile options panel in the UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 1
    bl_idname = "MT_PT_Curved_Floor_Tile_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "CURVED_FLOOR"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Blueprints")
        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        layout.label(text="Materials")
        layout.prop(scene_props, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(scene_props, 'tile_z', text="Height")
        layout.prop(scene_props, 'base_radius', text="Radius")
        layout.prop(scene_props, 'degrees_of_arc')
        layout.prop(scene_props, 'base_socket_side', text="Socket Side")
        layout.prop(scene_props, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(scene_props, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(scene_props, 'y_proportionate_scale', text="Width")
        row.prop(scene_props, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text="Width")
        layout.prop(scene_props, 'base_z', text="Height")

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_Curved_Tile:
    def update_curve_texture(self, context):
        """Change whether the texture on a curved floor tile follows the curve or not."""
        if self.tile_name:
            tile_collection = bpy.data.collections[self.tile_name]
            for obj in tile_collection.objects:
                obj_props = obj.mt_object_props
                if obj_props.is_displacement:
                    try:
                        mod = obj.modifiers['Simple_Deform']
                        if mod.show_render:
                            mod.show_render = False
                        else:
                            mod.show_render = True
                    except KeyError:
                        pass
        else:
            try:
                obj = context.active_object
                obj_props = obj.mt_object_props
                if obj_props.is_displacement:
                    try:
                        mod = obj.modifiers['Simple_Deform']
                        if mod.show_render:
                            mod.show_render = False
                        else:
                            mod.show_render = True
                    except KeyError:
                        pass
            except AttributeError:
                pass

    base_socket_side: EnumProperty(
        items=[
            ("INNER", "Inner", "", 1),
            ("OUTER", "Outer", "", 2)],
        name="Socket Side",
        default="INNER",
    )

    degrees_of_arc: FloatProperty(
        name="Degrees of arc",
        default=90,
        step=4500,
        precision=0,
        max=359.999,
        min=0
    )

    # Used for curved wall tiles
    base_radius: FloatProperty(
        name="Base inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0,
    )

    wall_radius: FloatProperty(
        name="Wall inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0
    )

    # used for curved floors
    curve_type: EnumProperty(
        items=[
            ("POS", "Positive", "", 1),
            ("NEG", "Negative", "", 2)],
        name="Curve type",
        default="POS",
        description="Whether the tile has a positive or negative curvature"
    )

    curve_texture: BoolProperty(
        name="Curve Texture",
        description="WARNING! You will need to make tile 3D to see the effects. Setting this to true will make the texture follow the curve of the tile. Useful for decorative elements, borders etc.",
        default=False,
        update=update_curve_texture
    )


class MT_OT_Make_Curved_Wall_Tile(Operator, MT_Curved_Tile, MT_Tile_Generator):
    """Create a Curved Wall Tile."""

    bl_idname = "object.make_curved_wall"
    bl_label = "Curved Wall"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "CURVED_WALL"

    # S Wall Props
    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base.")],
        default="CENTER")

    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

    wall_material: EnumProperty(
        items=create_material_enums,
        name="Wall Material")

    # @profile
    def exec(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        base_blueprint = self.base_blueprint
        wall_blueprint = self.main_part_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint == 'NONE':
            base = spawn_empty_base(tile_props)
        elif base_blueprint in ['PLAIN', 'PLAIN_S_WALL']:
            base = spawn_plain_base(tile_props)
        elif base_blueprint in ['OPENLOCK', 'OPENLOCK_S_WALL']:
            base = spawn_openlock_base(self, tile_props)

        if wall_blueprint == 'NONE':
            wall_core = None
        elif wall_blueprint == 'PLAIN':
            wall_core = spawn_plain_wall_cores(self, tile_props)
        elif wall_blueprint == 'OPENLOCK':
            wall_core = spawn_openlock_wall_cores(self, base, tile_props)

        if base_blueprint in {'OPENLOCK_S_WALL', 'PLAIN_S_WALL'}:
            # We temporarily override tile_props.base_size to generate floor core for S-Tiles.
            # It is easier to do it this way as the PropertyGroup.copy() method produces a dict
            orig_tile_size = []
            for c, v in enumerate(tile_props.tile_size):
                orig_tile_size.append(v)

            tile_props.tile_size = (
                tile_props.base_size[0],
                tile_props.base_size[1],
                scene_props.base_z + self.floor_thickness)
            floor_core = spawn_plain_floor_cores(self, tile_props)
            tile_props.tile_size = orig_tile_size
            self.finalise_tile(context, base, wall_core, floor_core)
        else:
            self.finalise_tile(context, base, wall_core)
        # profile.dump_stats(splitext(__file__)[0] + '.prof')
        return {'FINISHED'}

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return{'PASS_THROUGH'}
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

        layout.label(text="Blueprints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')

        layout.label(text="Materials")
        layout.prop(self, 'floor_material')
        layout.prop(self, 'wall_material')

        layout.label(text="Tile Properties")
        layout.prop(self, 'tile_z', text="Height")
        layout.prop(self, 'base_radius', text="Radius")
        layout.prop(self, 'degrees_of_arc')
        layout.prop(self, 'base_socket_side', text="Socket Side")
        layout.prop(self, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(self, 'tile_y', text="Width")

        if self.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.label(text="Floor Thickness")
            layout.prop(self, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(self, 'wall_position', text="")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(self, 'y_proportionate_scale', text="Width")
        row.prop(self, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(self, 'base_y', text="Width")
        layout.prop(self, 'base_z', text="Height")

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


class MT_OT_Make_Curved_Floor_Tile(Operator, MT_Curved_Tile, MT_Tile_Generator):
    """Create a Curved Floor Tile."""

    bl_idname = "object.make_curved_floor"
    bl_label = "Curved Floor"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "CURVED_FLOOR"

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

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
            core = spawn_plain_floor_cores(self, tile_props)

        self.finalise_tile(context, base, core)
        return {'FINISHED'}

    def execute(self, context):
        """Execute the operator."""
        super().execute(context)
        if not self.refresh:
            return{'PASS_THROUGH'}
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

        layout.label(text="Blueprints")
        layout.prop(self, 'base_blueprint')
        layout.prop(self, 'main_part_blueprint')

        layout.label(text="Materials")
        layout.prop(self, 'floor_material')

        layout.label(text="Tile Properties")
        layout.prop(self, 'tile_z', text="Height")
        layout.prop(self, 'base_radius', text="Radius")
        layout.prop(self, 'degrees_of_arc')
        layout.prop(self, 'base_socket_side', text="Socket Side")
        layout.prop(self, 'curve_texture', text="Curve Texture")

        layout.label(text="Core Properties")
        layout.prop(self, 'tile_y', text="Width")

        layout.label(text="Sync Proportions")
        row = layout.row()
        row.prop(self, 'y_proportionate_scale', text="Width")
        row.prop(self, 'z_proportionate_scale', text="Height")

        layout.label(text="Base Properties")
        layout.prop(self, 'base_y', text="Width")
        layout.prop(self, 'base_z', text="Height")

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


class MT_OT_Make_Openlock_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK curved base."""

    bl_idname = "object.make_openlock_curved_base"
    bl_label = "OpenLOCK Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_openlock_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_S_Wall_Straight_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an OpenLOCK S Wall curved base."""

    bl_idname = "object.make_openlock_s_wall_curved_base"
    bl_label = "OpenLOCK Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK_S_WALL"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_openlock_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved base."""

    bl_idname = "object.make_plain_curved_base"
    bl_label = "Plain Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_S_Wall_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved base."""

    bl_idname = "object.make_plain_s_wall_curved_base"
    bl_label = "Plain Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN_S_WALL"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved base."""

    bl_idname = "object.make_empty_curved_base"
    bl_label = "Empty Curved Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Plain_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved wall core."""

    bl_idname = "object.make_plain_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_WALL_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_plain_wall_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock curved wall core."""

    bl_idname = "object.make_openlock_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL', 'REGISTER'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_WALL_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]

        spawn_openlock_wall_cores(self, base, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Wall_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved wall core."""

    bl_idname = "object.make_empty_curved_wall_core"
    bl_label = "Curved Wall Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_WALL_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


class MT_OT_Make_Plain_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a plain curved wall core."""

    bl_idname = "object.make_plain_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "CURVED_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]
        spawn_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Openlock_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock curved wall core."""

    bl_idname = "object.make_openlock_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "OPENLOCK"
    mt_type = "CURVED_FLOOR_CORE"
    base_name: StringProperty()

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        base = bpy.data.objects[self.base_name]
        spawn_plain_floor_cores(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Curved_Floor_Core(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty curved wall core."""

    bl_idname = "object.make_empty_curved_floor_core"
    bl_label = "Curved Floor Core"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "CURVED_FLOOR_CORE"

    def execute(self, context):
        """Execute the operator."""
        return {'PASS_THROUGH'}


def spawn_plain_wall_cores(self, tile_props):
    """Spawn plain wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): core
    """
    offset = (tile_props.base_size[1] - tile_props.tile_size[1]) / 2
    tile_props.core_radius = tile_props.base_radius + offset
    textured_vertex_groups = ['Front', 'Back']
    core = spawn_wall_core(self, tile_props)
    material = tile_props.wall_material
    subsurf = add_subsurf_modifier(core)
    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    return core


def spawn_openlock_wall_cores(self, base, tile_props):
    """Spawn OpenLOCK wall cores into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        (bpy.types.Object): preview_core
    """
    offset = (tile_props.base_size[1] - tile_props.tile_size[1]) / 2
    tile_props.core_radius = tile_props.base_radius + offset

    core = spawn_wall_core(self, tile_props)
    subsurf = add_subsurf_modifier(core)
    cutters = spawn_openlock_wall_cutters(tile_props)

    kwargs = {
        "tile_props": tile_props}

    top_peg = spawn_openlock_top_pegs(
        base,
        **kwargs)

    set_bool_obj_props(top_peg, base, tile_props, 'UNION')
    set_bool_props(top_peg, core, 'UNION')

    for cutter in cutters:
        set_bool_obj_props(cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(cutter, core, 'DIFFERENCE')

    textured_vertex_groups = ['Front', 'Back']
    material = tile_props.wall_material
    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    activate(core.name)

    return core


def spawn_openlock_top_pegs(base, **kwargs):
    """Spawn top peg(s) for stacking wall tiles and position it.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: top peg(s)
    """
    tile_props = kwargs['tile_props']

    base_size = tile_props.base_size
    tile_size = tile_props.tile_size
    base_radius = tile_props.base_radius
    peg_source = load_openlock_top_peg(tile_props)
    peg_mesh = peg_source.data.copy()
    peg = bpy.data.objects.new("Top Peg", peg_mesh)
    add_object_to_collection(peg, tile_props.tile_name)
    bm = bmesh.new()
    bm.from_mesh(peg_mesh)
    bm = bmesh_array(
        source_obj=peg,
        source_bm=bm,
        count=1,
        use_relative_offset=False,
        use_constant_offset=True,
        constant_offset_displace=(0.505, 0, 0),
        use_merge_vertices=False,
        fit_type='FIXED_COUNT')

    base_location = base.location.copy()

    if tile_props.wall_position == 'CENTER':
        if base_radius >= 1:
            if tile_props.base_socket_side == 'INNER':
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(
                        -0.25,
                        base_radius + (base_size[1] / 2) + 0.06,
                        tile_size[2]),
                    space=peg.matrix_world)
            else:
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(
                        -0.25,
                        base_radius + (base_size[1] / 2) - 0.075,
                        tile_size[2]),
                    space=peg.matrix_world)

    elif tile_props.wall_position == 'SIDE':
        if base_radius >= 1:
            if tile_props.base_socket_side == 'INNER':
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(
                        -0.25,
                        base_radius + base_size[1] - 0.33,
                        tile_size[2]),
                    space=peg.matrix_world)
            else:
                bmesh.ops.translate(
                    bm,
                    verts=bm.verts,
                    vec=(
                        -0.25,
                        base_radius + base_size[1] - 0.235,
                        tile_size[2]),
                    space=peg.matrix_world)

    bmesh.ops.rotate(
        bm,
        cent=base_location,
        verts=bm.verts,
        matrix=Matrix.Rotation(radians(tile_props.degrees_of_arc / 2) * -1, 3, 'Z'),
        space=peg.matrix_world)
    bm.to_mesh(peg_mesh)
    bm.free()
    bpy.data.objects.remove(peg_source)
    return peg


def spawn_openlock_wall_cutters(tile_props):
    """Spawn OpenLOCK wall cutters into scene and position them.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        list[bpy.types.Objects]: cutters
    """
    deselect_all()

    tile_name = tile_props.tile_name

    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load side cutter
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.cutter.side']

    cutters = []

    # left side cutters
    left_cutter_bottom = data_to.objects[0].copy()
    left_cutter_bottom.name = 'X Neg Bottom.' + tile_name
    add_object_to_collection(left_cutter_bottom, tile_props.tile_name)

    right_cutter_bottom = left_cutter_bottom.copy()
    right_cutter_bottom.data = right_cutter_bottom.data.copy()
    right_cutter_bottom.name = 'X Pos Bottom.' + tile_name
    add_object_to_collection(right_cutter_bottom, tile_props.tile_name)

    cutters.extend([left_cutter_bottom, right_cutter_bottom])

    if tile_props.wall_position == 'SIDE':
        radius = tile_props.base_radius + (tile_props.base_size[1]) - (tile_props.tile_size[1] / 2) - 0.09
    else:
        radius = tile_props.base_radius + (tile_props.base_size[1] / 2)

    me = right_cutter_bottom.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.rotate(
        bm,
        verts=bm.verts,
        cent=right_cutter_bottom.location,
        matrix=Matrix.Rotation(radians(180), 3, 'Z'),
        space=right_cutter_bottom.matrix_world)

    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=(0, radius, 0.63),
        space=right_cutter_bottom.matrix_world)

    bmesh.ops.rotate(
        bm,
        verts=bm.verts,
        cent=right_cutter_bottom.location,
        matrix=Matrix.Rotation(radians(tile_props.degrees_of_arc) * -1, 3, 'Z'),
        space=right_cutter_bottom.matrix_world)

    bm.to_mesh(right_cutter_bottom.data)
    bm.free()

    me = left_cutter_bottom.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=(0, radius, 0.63),
        space=left_cutter_bottom.matrix_world)
    bm.to_mesh(left_cutter_bottom.data)
    bm.free()

    for cutter in cutters:
        array_mod = cutter.modifiers.new('Array', 'ARRAY')
        array_mod.use_relative_offset = False
        array_mod.use_constant_offset = True
        array_mod.constant_offset_displace = [0, 0, 2]
        array_mod.fit_type = 'FIT_LENGTH'
        array_mod.fit_length = tile_props.tile_size[2] - 1

    left_cutter_top = left_cutter_bottom.copy()
    left_cutter_top.name = 'X Neg Top.' + tile_name

    right_cutter_top = right_cutter_bottom.copy()
    right_cutter_top.name = 'X Pos Top.' + tile_name

    top_cutters = (left_cutter_top, right_cutter_top)

    for cutter in top_cutters:
        add_object_to_collection(cutter, tile_name)
        cutter.location[2] = cutter.location[2] + 0.75
        array_mod = cutter.modifiers['Array']
        array_mod.fit_length = tile_props.tile_size[2] - 1.8
        cutters.append(cutter)

    return cutters


def spawn_plain_base(self, tile_props):
    """Spawn a plain base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: tile base
    """
    radius = tile_props.base_radius
    deg = tile_props.degrees_of_arc
    height = tile_props.base_size[2]
    width = tile_props.base_size[1]
    arc = (deg / 360) * (2 * pi) * radius
    subdivs = get_subdivs(tile_props.subdivision_density, [arc, width, height])

    base = draw_curved_cuboid(
        tile_props.tile_name + '.base',
        radius,
        subdivs[0],
        deg,
        height,
        width)

    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name
    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_slot_cutter(self, base, tile_props, offset=0.236):
    """Spawns an openlock base slot cutter into the scene and positions it correctly.

    Args:
        base (bpy.types.Object): base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
        offset (float, optional): Offset from base end along x. Defaults to 0.236.

    Returns:
        bpy.types.Object: slot cutter
    """
    clip_side = tile_props.base_socket_side
    base_radius = tile_props.base_radius
    base_degrees = tile_props.degrees_of_arc

    cutter_w = 0.181
    cutter_h = 0.24

    if clip_side == 'INNER':
        cutter_radius = base_radius + 0.25
    else:
        cutter_radius = base_radius + tile_props.base_size[1] - 0.18 - 0.25

    bool_overlap = 0.001  # overlap amount to prevent errors

    cutter_inner_arc_len = (2 * pi * cutter_radius) / (360 / base_degrees) - (offset * 2)
    central_angle = degrees(cutter_inner_arc_len / cutter_radius)

    subdivs = get_subdivs(tile_props.subdivision_density, [cutter_inner_arc_len, cutter_w, cutter_h])

    slot_cutter = draw_curved_cuboid(
        'Slot.' + tile_props.tile_name,
        cutter_radius,
        subdivs[0],
        central_angle,
        cutter_h + bool_overlap,
        cutter_w
    )

    slot_cutter.location[2] = slot_cutter.location[2] - bool_overlap
    slot_cutter.rotation_euler[2] = slot_cutter.rotation_euler[2] - radians((base_degrees - central_angle) / 2)

    base.select_set(False)

    return slot_cutter


def spawn_openlock_base(self, tile_props):
    """Spawn OpenLOCK base into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base
    """
    radius = tile_props.base_radius
    deg = tile_props.degrees_of_arc
    height = tile_props.base_size[2]
    width = tile_props.base_size[1]
    arc = (deg / 360) * (2 * pi) * radius
    subdivs = get_subdivs(tile_props.subdivision_density, [arc, width, height])
    base = draw_curved_cuboid(
        tile_props.tile_name + '.base',
        radius,
        subdivs[0],
        deg,
        height,
        width)

    slot_cutter = spawn_openlock_base_slot_cutter(self, base, tile_props)
    set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(slot_cutter, base, 'DIFFERENCE')

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_props.tile_name

    spawn_openlock_base_clip_cutter(base, tile_props)

    bpy.context.view_layer.objects.active = base

    return base


def spawn_openlock_base_clip_cutter(base, tile_props):
    """Spawn base clip cutter into scene.

    Args:
        base (bpy.types.Object): tile base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: base clip cutter
    """
    scene = bpy.context.scene
    cursor_orig_loc = scene.cursor.location.copy()
    clip_side = tile_props.base_socket_side

    # load base cutter
    preferences = get_prefs()
    booleans_path = os.path.join(
        preferences.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.wall.base.cutter.clip_single']

    clip_cutter = data_to.objects[0]
    add_object_to_collection(clip_cutter, tile_props.tile_name)
    deselect_all()
    select(clip_cutter.name)

    if clip_side == 'INNER':
        radius = tile_props.base_radius + 0.25
    else:
        radius = tile_props.base_radius + tile_props.base_size[1] - 0.25

    mesh = clip_cutter.data.copy()
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if clip_side == 'OUTER':
        bmesh.ops.rotate(
            bm,
            verts=bm.verts,
            cent=clip_cutter.location,
            matrix=Matrix.Rotation(radians(180), 3, 'Z'),
            space=clip_cutter.matrix_world)

    bmesh.ops.translate(
        bm,
        verts=bm.verts,
        vec=(0, radius, 0),
        space=clip_cutter.matrix_world)

    num_cutters = modf((tile_props.degrees_of_arc - 22.5) / 22.5)[1]
    circle_center = cursor_orig_loc

    if num_cutters == 1:
        initial_rot = (tile_props.degrees_of_arc / 2)

    else:
        initial_rot = 22.5

    bmesh.ops.rotate(
        bm,
        cent=circle_center,
        verts=bm.verts,
        matrix=Matrix.Rotation(radians(initial_rot) * -1, 3, 'Z'),
        space=clip_cutter.matrix_world)

    i = 1
    source_geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    while i < num_cutters:
        # duplicate
        ret = bmesh.ops.duplicate(
            bm,
            geom=source_geom)
        geom = ret["geom"]
        dupe_verts = [ele for ele in geom if isinstance(ele, bmesh.types.BMVert)]
        del ret

        bmesh.ops.rotate(
            bm,
            cent=circle_center,
            verts=dupe_verts,
            matrix=Matrix.Rotation(radians(22.5 * i) * -1, 3, 'Z'),
            space=clip_cutter.matrix_world)
        i += 1

    bm.to_mesh(clip_cutter.data)
    bm.free()

    clip_cutter.name = 'Clip.' + base.name
    set_bool_obj_props(clip_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(clip_cutter, base, 'DIFFERENCE')

    return clip_cutter


def spawn_plain_floor_cores(self, tile_props):
    """Spawn preview and displacement cores into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: preview core
    """
    textured_vertex_groups = ['Top']
    tile_props.core_radius = tile_props.base_radius
    core = spawn_floor_core(self, tile_props)
    material = tile_props.floor_material
    subsurf = add_subsurf_modifier(core)
    convert_to_displacement_core(
        core,
        textured_vertex_groups,
        material,
        subsurf)

    return core


def spawn_floor_core(self, tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    angle = tile_props.degrees_of_arc
    radius = tile_props.core_radius
    width = tile_props.tile_size[1]
    height = tile_props.tile_size[2] - tile_props.base_size[2]
    inner_circumference = 2 * pi * radius
    floor_length = inner_circumference / (360 / angle)
    tile_name = tile_props.tile_name
    arc = (angle / 360) * (2 * pi) * radius
    native_subdivisions = get_subdivs(tile_props.subdivision_density, [arc, width, height])

    # Rather than creating our cores as curved objects we create them as straight cuboids
    # and then add a deform modifier. This allows us to not use the modifier when baking the
    # displacement texture by disabling it in render and thus being able to use
    # standard projections

    core = draw_rectangular_floor_core(
        (floor_length,
         width,
         height),
        native_subdivisions)

    core.name = tile_name + '.core'
    add_object_to_collection(core, tile_props.tile_name)

    tile_props.tile_size[0] = floor_length

    core.location = (
        core.location[0],
        core.location[1] + radius,
        core.location[2] + tile_props.base_size[2])

    mod = core.modifiers.new('Simple_Deform', type='SIMPLE_DEFORM')
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Z'
    mod.angle = radians(-angle)

    scene_props = bpy.context.scene.mt_scene_props

    # this controls whether the texture follows the curvature of the tile on render.
    # Useful for decorative elements.
    if scene_props.curve_texture:
        mod.show_render = False

    core.name = tile_props.tile_name + '.floor_core'

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core


def spawn_wall_core(self, tile_props):
    """Spawn core into scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: core
    """
    angle = tile_props.degrees_of_arc
    radius = tile_props.core_radius
    width = tile_props.tile_size[1]
    height = tile_props.tile_size[2] - tile_props.base_size[2]
    inner_circumference = 2 * pi * radius
    wall_length = inner_circumference / (360 / angle)
    tile_name = tile_props.tile_name
    arc = (angle / 360) * (2 * pi) * radius
    native_subdivisions = get_subdivs(tile_props.subdivision_density, [arc, width, height])

    # Rather than creating our cores as curved objects we create them as straight cuboids
    # and then add a deform modifier. This allows us to not use the modifier when baking the
    # displacement texture by disabling it in render and thus being able to use
    # standard projections

    core = draw_straight_wall_core(
        (wall_length,
         width,
         height),
        native_subdivisions)

    core.name = tile_name + '.core'

    add_object_to_collection(core, tile_props.tile_name)

    tile_props.tile_size[0] = wall_length

    core.location = (
        core.location[0],
        core.location[1] + radius,
        core.location[2] + tile_props.base_size[2])

    if tile_props.wall_position == 'SIDE':
        cursor = bpy.context.scene.cursor
        orig_cursor_loc = cursor.location.copy()
        cursor.location = core.location
        bm = bmesh.new()
        mesh = core.data.copy()
        bm.from_mesh(mesh)
        bmesh.ops.translate(
            bm,
            verts=bm.verts,
            vec=(
                0,
                (tile_props.base_size[1] / 2) - (tile_props.tile_size[1] / 2) - 0.09,
                0),
            space=core.matrix_world)
        bm.to_mesh(mesh)
        bm.free()
        core.data = mesh
        cursor.location = orig_cursor_loc

    mod = core.modifiers.new('Simple_Deform', type='SIMPLE_DEFORM')
    mod.deform_method = 'BEND'
    mod.deform_axis = 'Z'
    mod.angle = radians(-angle)
    mod.show_render = False
    core.name = tile_props.tile_name + '.wall_core'

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    return core
