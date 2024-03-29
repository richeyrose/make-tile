from typing import final
import bpy
import bmesh

from MakeTile.lib.bmturtle.commands import (
    create_turtle,
    finalise_turtle,
    home,
    pd,
    up,
)
from MakeTile.lib.bmturtle.helpers import (
    assign_verts_to_group,
    bm_deselect_all,
    bm_select_all,
    select_verts_in_bounds,
)

from bpy.types import Operator, Panel
from bpy.props import (
    FloatProperty,
    EnumProperty,
    IntProperty,
    BoolProperty,
)

from ..lib.utils.collections import add_object_to_collection

from .create_tile import (
    convert_to_displacement_core,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    get_subdivs,
    create_material_enums,
    add_subsurf_modifier,
    update_part_defaults,
)

from .tile_panels import (
    redo_tile_panel_header,
    scene_tile_panel_header,
    scene_tile_panel_footer,
    redo_tile_panel_footer,
)


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
        if hasattr(context.scene, "mt_scene_props"):
            return context.scene.mt_scene_props.tile_type == "MINI_BASE"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Shape")
        layout.prop(scene_props, "base_blueprint", text="")

        layout.label(text="Material")
        layout.prop(scene_props, "floor_material", text="")

        layout.label(text="Base Dimensions")
        if scene_props.base_blueprint in ("ROUND", "POLY"):
            layout.prop(scene_props, "base_diameter", text="Diameter")
            layout.prop(scene_props, "base_z", text="Height")

        if scene_props.base_blueprint != "RECT":
            layout.prop(scene_props, "segments")

        if scene_props.base_blueprint in ("RECT", "ROUNDED_RECT", "OVAL"):
            layout.prop(scene_props, "base_x")
            layout.prop(scene_props, "base_y")
            layout.prop(scene_props, "base_z")

        layout.prop(scene_props, "inset")
        layout.prop(scene_props, "wall_thickness")
        layout.prop(scene_props, "remove_doubles")

        scene_tile_panel_footer(scene_props, layout)


class MT_OT_Make_Mini_Base(Operator, MT_Tile_Generator):
    """Operator. Generates a straight wall tile with a customisable base and main part."""

    bl_idname = "object.make_mini_base"
    bl_label = "Mini Base"
    bl_options = {"UNDO", "REGISTER"}
    mt_blueprint = "CUSTOM"
    mt_type = "MINI_BASE"

    def update_base_blueprint(self, context):
        update_part_defaults(self, context)

    base_blueprint: EnumProperty(
        name="Base Blueprint",
        items=[
            ("ROUND", "Round", ""),
            ("POLY", "Polygonal", ""),
            ("RECT", "Rectangular", ""),
            ("ROUNDED_RECT", "Rounded Rectangle", ""),
            ("OVAL", "Oval", ""),
        ],
        default="RECT",
        update=update_base_blueprint
    )

    floor_material: EnumProperty(
        items=create_material_enums,
        name="Floor Material",
        description="Material to apply to top of base.",
    )

    base_diameter: FloatProperty(
        name="Base Diameter",
        default=2.0,
        step=10,
        precision=2,
        min=0.1
    )

    segments: IntProperty(
        name="Segments",
        description="For round bases set this to a high number.",
        default=32,
        min=3,
        max=64,
    )

    inset: FloatProperty(
        name="Inset",
        description="How far the top of the base is inset from the bottom.",
        default=0.1,
        step=0.05,
        min=0,
    )

    wall_thickness: FloatProperty(
        name="Wall Thickness",
        default=0.1,
        min=0.025,
        max=0.5,
        description="Thickness of wall for hollow bases.",
    )

    remove_doubles: BoolProperty(
        name="Remove Doubles",
        default=True,
        description="Can help get rid of glitches on round bases.",
    )

    def exec(self, context):
        base_blueprint = self.base_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props

        if base_blueprint in ["ROUND", "POLY"]:
            base = spawn_poly_base(tile_props)
        elif base_blueprint == "RECT":
            base = spawn_rect_base(tile_props)
        elif base_blueprint == "ROUNDED_RECT":
            base = spawn_rounded_rect_base(tile_props)
        elif base_blueprint == "OVAL":
            base = spawn_oval_base(tile_props)
        if not base:
            self.delete_tile_collection(self.tile_name)
            self.report({"INFO"}, "Could not generate base. Cancelling")
            return {"CANCELLED"}

        self.finalise_tile(context, base)
        return {"FINISHED"}

    def execute(self, context):
        super().execute(context)
        if not self.refresh:
            return {"PASS_THROUGH"}
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
        layout.label(text="Base Shape")
        layout.prop(self, "base_blueprint", text="")
        layout.label(text="Material")
        layout.prop(self, "floor_material", text="")

        if self.base_blueprint in ("ROUND", "POLY"):
            layout.prop(self, "base_diameter", text="Diameter")
            layout.prop(self, "base_z", text="Height")

        if self.base_blueprint != "RECT":
            layout.prop(self, "segments")

        if self.base_blueprint in ("RECT", "ROUNDED_RECT", "OVAL"):
            layout.prop(self, "base_x")
            layout.prop(self, "base_y")
            layout.prop(self, "base_z")

        layout.prop(self, "inset")
        layout.prop(self, "wall_thickness")
        layout.prop(self, "remove_doubles")

        redo_tile_panel_footer(self, layout)


def spawn_poly_base(tile_props):
    """Spawn a polygonal base into the scene. Can also be used to create round or square bases.

    Args:
        context (bpy.Context): Context
        tile_props (tile_props): tile props

    Returns:
        bpy.types.obj: Base
    """
    tile_name = tile_props.tile_name

    base = draw_poly_base(tile_props)
    base.name = tile_name + ".base"

    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = "BASE"
    obj_props.tile_name = tile_name

    subsurf = add_subsurf_modifier(base)

    # hollow base
    base_cutter = spawn_poly_base_cutter(tile_props)
    set_bool_obj_props(base_cutter, base, tile_props, "DIFFERENCE")
    set_bool_props(base_cutter, base, "DIFFERENCE")

    textured_vertex_groups = ["Top"]
    material = tile_props.floor_material
    convert_to_displacement_core(
        base, textured_vertex_groups, material, subsurf)

    bpy.context.view_layer.objects.active = base
    return base


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
    height = tile_props.base_size[2] - wall_thickness
    inset = tile_props.inset

    bm, hollow_bool = create_turtle("Hollow")

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius - (inset / 2),
        depth=height,
    )
    bmesh.ops.translate(bm, vec=(0, 0, -0.01), verts=bm.verts)
    finalise_turtle(bm, hollow_bool)
    return hollow_bool


def spawn_rect_base(tile_props):
    """Spawn a rectangular base into the scene.

    Args:
        context (bpy.Context): Context
        tile_props (tile_props): tile props

    Returns:
        bpy.types.Object: Base
    """
    tile_name = tile_props.tile_name

    base = draw_rect_base(tile_props)
    base.name = tile_name + ".base"

    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = "BASE"
    obj_props.tile_name = tile_name

    subsurf = add_subsurf_modifier(base)

    # hollow base
    base_cutter = spawn_rect_base_cutter(tile_props)
    set_bool_obj_props(base_cutter, base, tile_props, "DIFFERENCE")
    set_bool_props(base_cutter, base, "DIFFERENCE")

    textured_vertex_groups = ["Top"]
    material = tile_props.floor_material
    convert_to_displacement_core(
        base, textured_vertex_groups, material, subsurf)

    bpy.context.view_layer.objects.active = base
    return base


def spawn_rect_base_cutter(tile_props):
    """Spawn a cutter for hollowing rectangular bases.

    Args:
        tile_props (tile_props): tile props

    Returns:
        bpy.types.Object: cutter object
    """
    width = (tile_props.base_size[0] / 2) - tile_props.wall_thickness
    length = (tile_props.base_size[1] / 2) - tile_props.wall_thickness
    height = (tile_props.base_size[2]) - tile_props.wall_thickness
    inset = tile_props.inset

    bm, cutter = create_turtle("Hollow")

    bottom = bmesh.ops.create_grid(
        bm,
        x_segments=1,
        y_segments=1,
        size=width)
    ratio = length / width
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, -0.001), verts=bottom['verts'])
    top = bmesh.ops.create_grid(
        bm,
        x_segments=1,
        y_segments=1,
        size=width)

    bmesh.ops.translate(bm, vec=(0, 0, height), verts=top['verts'])
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=top['verts'])

    width_ratio = ((width-inset)/width)
    length_ratio = ((length-inset)/length)
    bmesh.ops.scale(bm, vec=(width_ratio, length_ratio, 1), verts=top['verts'])

    bm.select_mode = {"EDGE"}
    edges = bm.edges
    for e in edges:
        if e.is_boundary:
            e.select_set(True)
    edges = [e for e in bm.edges if e.select]
    bmesh.ops.bridge_loops(bm, edges=edges)

    finalise_turtle(bm, cutter)
    return cutter


def draw_rect_base(tile_props):
    """Draw a rectangualr base.

    Args:
        tile_props (tile_props): Tile Props

    Returns:
        bpy.types.Object: Base object
    """
    width = tile_props.base_size[0] / 2
    length = tile_props.base_size[1] / 2
    height = tile_props.base_size[2]
    inset = tile_props.inset
    margin = tile_props.texture_margin
    subdivs = get_subdivs(tile_props.subdivision_density,
                          [width, length, height])

    vert_groups = ["Top", "Untextured"]
    bm, base = create_turtle("Base", vert_groups)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active

    bottom = bmesh.ops.create_grid(
        bm,
        x_segments=subdivs[0],
        y_segments=subdivs[1],
        size=width)
    ratio = length / width
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=bm.verts)

    top = bmesh.ops.create_grid(
        bm, x_segments=subdivs[0],
        y_segments=subdivs[1],
        size=width)
    for v in top['verts']:
        v.select_set(True)
    bm.select_flush(True)
    top_faces = [f for f in bm.faces if f.select]

    bm_deselect_all(bm)
    bmesh.ops.translate(bm, vec=(0, 0, height), verts=top['verts'])
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=top['verts'])

    width_ratio = ((width-inset)/width)
    length_ratio = ((length-inset)/length)
    bmesh.ops.scale(bm, vec=(width_ratio, length_ratio, 1), verts=top['verts'])

    bm.select_mode = {"EDGE"}
    edges = bm.edges
    for e in edges:
        if e.is_boundary:
            e.select_set(True)
    edges = [e for e in bm.edges if e.select]
    bmesh.ops.bridge_loops(bm, edges=edges)

    bm.select_mode = {"FACE"}
    bm_deselect_all(bm)

    ret = bmesh.ops.inset_region(bm, faces=top_faces, thickness=margin)
    bm.select_mode = {"VERT"}
    for f in top_faces:
        f.select_set(True)

    verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(verts, base, deform_groups, "Top")

    if tile_props.remove_doubles:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    finalise_turtle(bm, base)

    return base


def spawn_rounded_rect_base(tile_props):
    """Spawn a rounded rectangular base into the scene.

    Args:
        tile_props (tile_props): tile props

    Returns:
        bpy.types.Object: Base object.
    """
    tile_name = tile_props.tile_name
    base = draw_rounded_rect_base(tile_props)
    base.name = tile_name + ".base"

    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = "BASE"
    obj_props.tile_name = tile_name

    subsurf = add_subsurf_modifier(base)

    base_cutter = spawn_rounded_rect_base_cutter(tile_props)
    set_bool_obj_props(base_cutter, base, tile_props, "DIFFERENCE")
    set_bool_props(base_cutter, base, "DIFFERENCE")

    textured_vertex_groups = ["Top"]
    material = tile_props.floor_material
    convert_to_displacement_core(
        base, textured_vertex_groups, material, subsurf)
    bpy.context.view_layer.objects.active = base
    return base


def spawn_rounded_rect_base_cutter(tile_props):
    """Spawn a rounded rectangular base cutter for hollowing base.

    Args:
        tile_props (tile_props): Tile Props

    Returns:
        bpy.types.Object: Base Cutter Object.
    """
    wall_thickness = tile_props.wall_thickness

    if tile_props.base_size[0] < tile_props.base_size[1]:
        radius = (tile_props.base_size[0] / 2) - wall_thickness
        length = tile_props.base_size[1] - \
            tile_props.base_size[0] - wall_thickness
    else:
        radius = (tile_props.base_size[1] / 2) - wall_thickness
        length = tile_props.base_size[0] - \
            tile_props.base_size[1] - wall_thickness
    segments = tile_props.segments
    height = tile_props.base_size[2] - wall_thickness
    inset = tile_props.inset
    return draw_rounded_cuboid(
        radius, length, segments, height, inset, "Hollow", -0.001
    )


def spawn_oval_base(tile_props):
    """Spawn an oval base into the scene

    Args:
        tile_props (tile_props): tile props

    Returns:
        bpy.types.Object: base
    """
    tile_name = tile_props.tile_name
    base = draw_oval_base(tile_props)
    base.name = tile_name + ".base"

    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = "BASE"
    obj_props.tile_name = tile_name

    subsurf = add_subsurf_modifier(base)

    base_cutter = spawn_oval_base_cutter(tile_props)
    set_bool_obj_props(base_cutter, base, tile_props, "DIFFERENCE")
    set_bool_props(base_cutter, base, "DIFFERENCE")

    textured_vertex_groups = ["Top"]
    material = tile_props.floor_material
    convert_to_displacement_core(
        base, textured_vertex_groups, material, subsurf)

    bpy.context.view_layer.objects.active = base
    return base


def spawn_oval_base_cutter(tile_props):
    """Spawn an oval base cutter.

    Args:
        tile_props (tile_props): tile props

    Returns:
        bpy.types.Object: object
    """
    wall_thickness = tile_props.wall_thickness
    radius = (tile_props.base_size[0] / 2) - wall_thickness
    length = (tile_props.base_size[1] / 2) - wall_thickness
    segments = tile_props.segments
    height = tile_props.base_size[2] - wall_thickness
    inset = tile_props.inset

    bm, hollow_bool = create_turtle("Hollow")

    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius - (inset / 2),
        depth=height,
    )
    bmesh.ops.translate(bm, vec=(0, 0, -0.01), verts=bm.verts)

    ratio = length / radius
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=bm.verts)

    finalise_turtle(bm, hollow_bool)
    return hollow_bool


def draw_rounded_rect_base(tile_props):
    """Draw a rounded rectangular base.

    Args:
        tile_props (tile_props): Tile props.

    Returns:
        bpy.types.Object: Rectangualr Base Object
    """
    if tile_props.base_size[0] < tile_props.base_size[1]:
        radius = tile_props.base_size[0] / 2
        length = tile_props.base_size[1] - tile_props.base_size[0]
    else:
        radius = tile_props.base_size[1] / 2
        length = tile_props.base_size[0] - tile_props.base_size[1]
    segments = tile_props.segments
    height = tile_props.base_size[2]
    inset = tile_props.inset
    base_template = draw_rounded_cuboid(
        radius, length, segments, height, inset, "Template"
    )

    # create grid
    base = generate_grid_base(base_template, tile_props)

    # delete template
    bpy.data.objects.remove(base_template)

    return base


def draw_rounded_cuboid(radius, length, segments, height, inset, name, offset=0.0):
    """Draw a rounded cuboid object.

    Args:
        radius (float): radius
        length (float): length
        segments (int): number of segments on rounded part
        height (float): height
        inset (float): amount top is inset
        name (str): Name
        offset (float, optional): z_offset. Defaults to 0.0

    Returns:
        bpy.tyes.Object: Rounded Cuboid
    """
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()

    bm, rounded_rect = create_turtle(name)
    bmesh.ops.create_cone(
        bm,
        cap_ends=False,
        segments=segments,
        radius1=radius,
        radius2=radius - inset,
        depth=height,
    )

    bmesh.ops.translate(bm, vec=(0, 0, (height / 2) + offset), verts=bm.verts)

    bm.select_mode = {"FACE"}
    bm_deselect_all(bm)
    bm.select_mode = {"VERT"}
    select_verts_in_bounds(
        lbound=(origin[0] - radius, origin[1] - radius, origin[2]),
        ubound=(origin[0] + radius, origin[1], origin[2] + height),
        buffer=0.01,
        bm=bm,
    )
    bm.select_flush(True)
    faces = [f for f in bm.faces if f.select]
    ret = bmesh.ops.split(bm, geom=faces)
    bm_deselect_all(bm)

    faces = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace)]
    for f in bm.faces:
        if f in faces:
            f.select_set(True)
    verts = [v for v in bm.verts if v.select]

    bmesh.ops.translate(bm, vec=(0, -length, 0), verts=verts)
    bm_deselect_all(bm)

    select_verts_in_bounds(
        lbound=(origin[0] - radius, origin[1] - length, origin[2]),
        ubound=(origin[0] - radius + inset, origin[1], origin[2] + height),
        buffer=0.01,
        bm=bm,
    )
    bm.select_flush(True)
    edges = [e for e in bm.edges if e.select]
    bmesh.ops.bridge_loops(bm, edges=edges)
    bm_deselect_all(bm)

    select_verts_in_bounds(
        lbound=(origin[0] + radius - inset, origin[1] - length, origin[2]),
        ubound=(origin[0] + radius, origin[1], origin[2] + height),
        buffer=0.01,
        bm=bm,
    )
    bm.select_flush(True)
    edges = [e for e in bm.edges if e.select]
    bmesh.ops.bridge_loops(bm, edges=edges)
    bm_deselect_all(bm)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges])
    bmesh.ops.translate(bm, vec=(0, length / 2, 0), verts=bm.verts)

    finalise_turtle(bm, rounded_rect)
    return rounded_rect


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

    bm, base_template = create_turtle("template")
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius - inset,
        depth=height,
    )
    bmesh.ops.translate(bm, vec=(0, 0, height / 2), verts=bm.verts)

    finalise_turtle(bm, base_template)

    tile_props.base_size[0] = radius
    base = generate_grid_base(base_template, tile_props)

    # delete template
    bpy.data.objects.remove(base_template)

    return base


def draw_oval_base(tile_props):
    """Draw an Oval Base

    Args:
        tile_props (tile_props): tile_props

    Returns:
        bpy.types.Object: Object
    """
    radius = tile_props.base_size[0] / 2
    length = tile_props.base_size[1] / 2
    segments = tile_props.segments
    height = tile_props.base_size[2]
    inset = tile_props.inset

    bm, base_template = create_turtle("template")
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=segments,
        radius1=radius,
        radius2=radius - inset,
        depth=height,
    )
    bmesh.ops.translate(bm, vec=(0, 0, height / 2), verts=bm.verts)

    ratio = length / radius
    bmesh.ops.scale(bm, vec=(1, ratio, 1), verts=bm.verts)

    finalise_turtle(bm, base_template)
    base = generate_grid_base(base_template, tile_props)

    # delete template
    bpy.data.objects.remove(base_template)

    return base


def generate_grid_base(base_template, tile_props):
    """Generates a base with the top subdivided into an equal grid when passed a template object.

    Args:
        base_template (bpy.types.Object): Template object
        tile_props (tile_props): Tile props

    Returns:
        bpy.types.Object: Object
    """
    if base_template.dimensions[0] > base_template.dimensions[1]:
        size = base_template.dimensions[0] / 2
    else:
        size = base_template.dimensions[1] / 2
    margin = tile_props.texture_margin
    height = base_template.dimensions[2]
    subdivs = get_subdivs(tile_props.subdivision_density, [size, size, height])
    turtle = bpy.context.scene.cursor
    origin = turtle.location.copy()
    # create grid
    bm, base = create_turtle("base")
    ret = bmesh.ops.create_grid(
        bm, x_segments=subdivs[0], y_segments=subdivs[1], size=size + 0.5
    )

    bmesh.ops.translate(bm, vec=[0, 0, -0.01], verts=ret["verts"])
    bm.select_mode = {"FACE"}
    pd(bm)
    bm_select_all(bm)
    up(bm, height, False)
    finalise_turtle(bm, base)

    # add modifier and use template to create an intersect
    bool = base.modifiers.new("temp", "BOOLEAN")
    bool.solver = "EXACT"
    bool.operation = "INTERSECT"
    bool.object = base_template

    # apply modifier
    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = base.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
    base.modifiers.remove(bool)
    base.data = mesh_from_eval

    # create new bmesh from evaluated mesh
    me = base.data
    bm = bmesh.new()
    bm.from_mesh(me)

    vert_groups = ["Top", "Untextured"]
    for group in vert_groups:
        base.vertex_groups.new(name=group)

    # create vertex group layer
    bm.verts.layers.deform.verify()
    deform_groups = bm.verts.layers.deform.active

    bm.select_mode = {"FACE"}
    faces = [f for f in bm.faces if f.select]
    bm_deselect_all(bm)

    # inset for texture margin
    ret = bmesh.ops.inset_region(bm, faces=faces, thickness=margin)
    bm.select_mode = {"VERT"}
    select_verts_in_bounds(
        lbound=(origin[0] - size, origin[1] - size, origin[2] + height),
        ubound=(origin[0] + size, origin[1] + size, origin[2] + height),
        buffer=0.01,
        bm=bm,
    )
    bm.select_flush(True)
    faces = [f for f in bm.faces if f.select and f not in ret["faces"]]
    bm_deselect_all(bm)
    bm.select_mode = {"FACE"}
    for f in bm.faces:
        if f in faces:
            f.select_set(True)
    bm.select_flush(True)

    verts = [v for v in bm.verts if v.select]
    assign_verts_to_group(verts, base, deform_groups, "Top")

    if tile_props.remove_doubles:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

    bm.to_mesh(me)
    bm.free()
    home(base)
    return base
