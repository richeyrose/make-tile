from email.encoders import encode_noop
import os
from math import radians
from xmlrpc.client import boolean
from MakeTile.lib.bmturtle.commands import arc, create_turtle, dn, finalise_turtle, home, pd, pu, up
from MakeTile.lib.bmturtle.helpers import assign_verts_to_group, bm_deselect_all, bm_select_all, select_verts_in_bounds

import bpy
import bmesh

from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    BoolProperty)

from .. utils.registration import get_prefs
from .. lib.utils.collections import (
    add_object_to_collection)

from ..lib.bmturtle.scripts import (
    draw_straight_wall_core,
    draw_cuboid,
    draw_rectangular_floor_core)

from .create_tile import (
    spawn_empty_base,
    convert_to_displacement_core,
    set_bool_obj_props,
    set_bool_props,
    load_openlock_top_peg,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    create_wall_position_enums,
    add_subsurf_modifier)

from .tile_panels import (
    redo_straight_tiles_panel,
    redo_tile_panel_header,
    scene_tile_panel_header,
    scene_tile_panel_footer,
    scene_straight_tiles_panel,
    redo_tile_panel_footer)

class MT_PT_Mini_Base_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Mini_Base_Panel"
    bl_description = "Options to configure the dimensions of a miniature base."

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "MINI_BASE"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout
        blueprints = ['base_blueprint']

        scene_tile_panel_header(scene_props, layout, blueprints, 'BASE')
        layout.prop(scene_props, 'floor_material')

        if scene_props.base_blueprint in ('ROUND', 'POLY'):
            layout.prop(scene_props, 'base_diameter', text="Diameter")
            layout.prop(scene_props, 'segments', )
            layout.prop(scene_props, 'base_z', text="Height")

        elif scene_props.base_blueprint in ('RECT', 'ROUNDED_RECT', 'OVAL'):
            layout.prop(scene_props, 'base_x')
            layout.prop(scene_props, 'base_y')
            layout.prop(scene_props, 'base_z')

        layout.prop(scene_props, 'inset')
        layout.prop(scene_props, 'wall_thickness')
        layout.prop(scene_props, 'remove_doubles')

        scene_tile_panel_footer(scene_props, layout)

class MT_OT_Make_Mini_Base(Operator, MT_Tile_Generator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_mini_base"
    bl_label = "Mini Base"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "MINI_BASE"

    base_blueprint: EnumProperty(
        name="Base Blueprint",
        items=[
            ('ROUND', 'Round', ''),
            ('POLY', 'Polygonal', ''),
            ('RECT', 'Rectangular', ''),
            ('ROUNDED_RECT', 'Rounded Ractangle', ''),
            ('OVAL', 'Oval', '')],
        default='RECT'
    )

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material")

    base_diameter: FloatProperty(
        name="Base Diameter",
        default=2.0,
        step=10,
        precision=1,
        min=0.1,
    )

    segments: IntProperty(
        name="Segments",
        default=32,
        min=3,
        max=64
    )

    inset: FloatProperty(
        name="Inset",
        default=0.1,
        step=0.05,
        min=0
    )

    wall_thickness: FloatProperty(
        name="Wall Thickness",
        default=0.1,
        min=0.025,
        max=0.5,
        description="Thickness of wall for hollow bases."
    )

    remove_doubles: BoolProperty(
        name="Remove Doubles",
        default=True,
        description="Can help get rid of glitches on round bases.")

    def exec(self, context):
        base_blueprint = self.base_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint in ['ROUND', 'POLY']:
            base = spawn_poly_base(self, context, tile_props)
        elif base_blueprint == 'RECT':
            base = spawn_rect_base(self, context, tile_props)
        elif base_blueprint == 'ROUNDED_RECT':
            base = spawn_rounded_rect_base(self, context, tile_props)
        elif base_blueprint == 'OVAL':
            base = spawn_oval_base(self, context, tile_props)
        if not base:
            self.delete_tile_collection(self.tile_name)
            self.report({'INFO'}, "Could not generate base. Cancelling")
            return {'CANCELLED'}

        self.finalise_tile(context, base)
        return {'FINISHED'}

    def execute(self, context):
        super().execute(context)
        if not self.refresh:
            return {'PASS_THROUGH'}
        return self.exec(context)

    def init(self, context):
        super().init(context)
        tile_collection = bpy.data.collections[self.tile_name]
        tile_props = tile_collection.mt_tile_props
        tile_props.collection_type = "TILE"
        tile_props.base_size = (self.base_x, self.base_y, self.base_z)

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        blueprints = ['base_blueprint']
        redo_tile_panel_header(self, layout, blueprints, 'BASE')

        layout.prop(self, 'floor_material')

        if self.base_blueprint in ('ROUND', 'POLY'):
            layout.prop(self, 'base_diameter', text="Diameter")
            layout.prop(self, 'segments', )
            layout.prop(self, 'base_z', text="Height")

        elif self.base_blueprint in ('RECT', 'ROUNDED_RECT', 'OVAL'):
            layout.prop(self, 'base_x')
            layout.prop(self, 'base_y')
            layout.prop(self, 'base_z')

        layout.prop(self, 'inset')
        layout.prop(self, 'wall_thickness')
        layout.prop(self, 'remove_doubles')

        redo_tile_panel_footer(self, layout)

def spawn_poly_base_cutter(tile_props):
    """Spawn a cutter used for hollowing out polygonal bases.

    Args:
        tile_props (tiel_props): tile props

    Returns:
        bpy.Types.object: cutter object
    """
    wall_thickness = tile_props.wall_thickness
    radius = (tile_props.base_diameter / 2) - wall_thickness
    segments = tile_props.segments
    height = tile_props.base_size[2]-wall_thickness
    inset = tile_props.inset

    bm, hollow_bool = create_turtle('Hollow')

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius-(inset/2),
        depth=height)
    bmesh.ops.translate(
        bm,
        vec=(0, 0, -0.01),
        verts=bm.verts)
    finalise_turtle(bm, hollow_bool)
    return hollow_bool

def spawn_poly_base(self, context, tile_props):
    """Spawn a polygonal base into the scene. Can also be used to create round or square bases.

    Args:
        context (bpy.Context): Context
        tile_props (tile_props): tile props

    Returns:
        bpy.types.obj: Base
    """
    tile_name = tile_props.tile_name

    base = draw_poly_base(tile_props)
    base.name = tile_name + '.base'

    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name

    subsurf = add_subsurf_modifier(base)

    # hollow base
    base_cutter = spawn_poly_base_cutter(tile_props)
    set_bool_obj_props(base_cutter, base, tile_props, 'DIFFERENCE')
    set_bool_props(base_cutter, base, 'DIFFERENCE')

    textured_vertex_groups = ['Top']
    material = tile_props.floor_material
    convert_to_displacement_core(
        base,
        textured_vertex_groups,
        material,
        subsurf)

    bpy.context.view_layer.objects.active = base
    return base

def draw_poly_base(tile_props):
    """Draw a polygonal base. Can also be used to draw round or square bases.

    Args:
        tile_props (tile_props): tile props

    Returns:
        bpy.Types.object: object
    """
    radius = tile_props.base_diameter / 2
    segments = tile_props.segments
    height = tile_props.base_size[2]
    inset = tile_props.inset
    margin = tile_props.texture_margin
    subdivs = get_subdivs(tile_props.subdivision_density, [radius, radius, height])

    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    bm, base_template = create_turtle('template')
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius-inset,
        depth=height)
    bmesh.ops.translate(
        bm,
        vec=(0, 0, height / 2),
        verts=bm.verts)

    finalise_turtle(bm, base_template)

    # Create the mesh which will be used as our actual base out of a grid.
    bm, base = create_turtle('base')

    # create a grid and extrude it upward
    ret = bmesh.ops.create_grid(
        bm,
        x_segments=subdivs[0],
        y_segments=subdivs[1],
        size=radius+0.5)

    bmesh.ops.translate(bm, vec=[0, 0, -0.01], verts=ret['verts'])
    bm.select_mode = {'FACE'}
    pd(bm)
    bm_select_all(bm)
    up(bm, height, False)
    finalise_turtle(bm, base)

    # add modifier and use template to create an intersect
    bool = base.modifiers.new('temp', 'BOOLEAN')
    bool.solver = 'EXACT'
    bool.operation = 'INTERSECT'
    bool.object = base_template

    # apply modifier
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = base.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
    base.modifiers.remove(bool)
    base.data = mesh_from_eval

    # delete template
    bpy.data.objects.remove(base_template)

    # create new bmesh from evaluated mesh
    me = base.data
    bm = bmesh.new()
    bm.from_mesh(me)

    vert_groups = ['Top', 'Untextured']
    for group in vert_groups:
        base.vertex_groups.new(name=group)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active

    bm.select_mode = {'FACE'}
    faces = [f for f in bm.faces if f.select]
    bm_deselect_all(bm)

    # inset for texture margin
    ret = bmesh.ops.inset_region(bm, faces=faces, thickness=margin)
    bm.select_mode = {'VERT'}
    select_verts_in_bounds(
        lbound=(
            origin[0] - radius,
            origin[1] - radius,
            origin[2] + height),
        ubound=(
            origin[0] + radius,
            origin[1] + radius,
            origin[2] + height),
        buffer=0.01,
        bm=bm)
    bm.select_flush(True)
    faces = [f for f in bm.faces if f.select and f not in ret['faces']]
    bm_deselect_all(bm)
    bm.select_mode = {'FACE'}
    for f in bm.faces:
        if f in faces:
            f.select_set(True)
    bm.select_flush(True)

    verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(verts, base, deform_groups, 'Top')

    bmesh.ops.remove_doubles(
        bm,
        verts=bm.verts,
        dist=0.0001)

    bm.to_mesh(me)
    bm.free()

    return base

def spawn_rect_base(self, context, tile_props):
    return None

def spawn_rounded_rect_base(self, context, tile_props):
    return None

def spawn_oval_base(self, context, tile_props):
    return None
