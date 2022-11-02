import os
import bpy

from bpy.types import Operator, Panel
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatProperty)

from ..utils.registration import get_prefs

from .. lib.utils.collections import (
    add_object_to_collection)
from .. lib.bmturtle.scripts import draw_cuboid

from ..lib.utils.selection import activate
from .create_tile import (
    spawn_empty_base,
    convert_to_displacement_core,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    create_material_enums,
    add_subsurf_modifier)

from .apex_roof import draw_apex_roof_top, draw_apex_base
from .shed_roof import draw_shed_base, draw_shed_roof_top
from .butterfly_roof import draw_butterfly_base, draw_butterfly_roof_top

'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


class MT_PT_Roof_Panel(Panel):
    """Draw a tile options panel in UI."""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_order = 2
    bl_idname = "MT_PT_Roof_Panel"
    bl_description = "Options to configure the dimensions of a tile"

    @classmethod
    def poll(cls, context):
        """Check tile_type."""
        if hasattr(context.scene, 'mt_scene_props'):
            return context.scene.mt_scene_props.tile_type == "ROOF"
        return False

    def draw(self, context):
        """Draw the Panel."""
        scene = context.scene
        scene_props = scene.mt_scene_props

        layout = self.layout
        layout.label(text="Roof Type")
        layout.prop(scene_props, 'roof_type', text="")
        layout.prop(scene_props, 'base_blueprint', text="Gable")
        layout.prop(scene_props, 'main_part_blueprint', text="Rooftop")

        row = layout.row()
        '''
        row.prop(scene_props, 'draw_gables')
        row.prop(scene_props, 'draw_rooftop')
        '''
        layout.label(text="Materials")
        if scene_props.base_blueprint != "NONE":
            layout.prop(scene_props, 'gable_material')
        if scene_props.main_part_blueprint != "NONE":
            layout.prop(scene_props, 'rooftop_material')

        # layout.label(text="Socket Types")
        layout.label(text="Bottom Socket")
        layout.prop(scene_props, 'base_bottom_socket_type', text="")
        # layout.prop(roof_props, 'base_side_socket_type')
        # layout.prop(roof_props, 'gable_socket_type')
        layout.prop(scene_props, 'generate_suppports')

        layout.label(text="Roof Footprint")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')

        layout.label(text="Roof Properties")

        layout.prop(scene_props, 'roof_pitch', text="Roof Pitch")
        layout.prop(scene_props, 'end_eaves_pos', text="Positive End Eaves")
        layout.prop(scene_props, 'end_eaves_neg', text="Negative End Eaves")
        layout.prop(scene_props, 'roof_thickness')

        layout.prop(scene_props, 'side_eaves', text="Side Eaves")
        layout.prop(scene_props, 'base_z', text="Base Height")

        layout.label(text="Wall Inset Correction")
        layout.prop(scene_props, 'inset_dist', text="Inset Distance")
        row = layout.row()
        row.prop(scene_props, 'inset_x_neg', text="X Neg")
        row.prop(scene_props, 'inset_x_pos', text="X Pos")
        row.prop(scene_props, 'inset_y_neg', text="Y Neg")
        row.prop(scene_props, 'inset_y_pos', text="Y Pos")

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.label(text="UV Island Margin")
        layout.prop(scene_props, 'UV_island_margin', text="")

        layout.operator('scene.reset_tile_defaults')


class MT_OT_Make_Roof(Operator, MT_Tile_Generator):
    """Operator. Generates a roof tile."""

    bl_idname = "object.make_roof"
    bl_label = "Roof"
    bl_options = {'UNDO', 'REGISTER'}
    mt_blueprint = "CUSTOM"
    mt_type = "ROOF"

    roof_type: EnumProperty(
        items=[
            ("APEX", "Apex", "", 1),
            ("BUTTERFLY", "Butterfly", "", 2),
            ("SHED", "Shed", "", 3)],
        name="Roof Type")

    roof_pitch: FloatProperty(
        name="Roof Pitch",
        default=45,
        step=1,
        min=0
    )

    end_eaves_pos: FloatProperty(
        name="End Eaves Positive",
        default=0.1,
        step=0.1,
        min=0
    )

    end_eaves_neg: FloatProperty(
        name="End Eaves Negative",
        default=0.1,
        step=0.1,
        min=0
    )

    side_eaves: FloatProperty(
        name="Side Eaves",
        default=0.2755,
        step=0.1,
        min=0
    )

    roof_thickness: FloatProperty(
        name="Roof Thickness",
        default=0.1,
        step=0.05,
        min=0
    )

    inset_dist: FloatProperty(
        name="Inset Distance",
        description="Distance core is usually inset from the base of a wall",
        default=0.09,
        min=0
    )

    inset_x_neg: BoolProperty(
        name="Inset X Neg",
        default=True)

    inset_x_pos: BoolProperty(
        name="Inset X Pos",
        default=True)

    inset_y_neg: BoolProperty(
        name="Inset Y Neg",
        default=True)

    inset_y_pos: BoolProperty(
        name="Inset Y Pos",
        default=True)

    base_bottom_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        name="Base Bottom Socket",
        default='OPENLOCK')

    base_side_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        default='NONE',
        name="Base Side Socket")

    gable_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        default='NONE',
        name="Gable Side Socket")

    gable_material: EnumProperty(
        items=create_material_enums,
        name="Gable Material")

    rooftop_material: EnumProperty(
        items=create_material_enums,
        name="Rooftop Material")

    # @profile
    def exec(self, context):
        gable_blueprint = self.base_blueprint
        rooftop_blueprint = self.main_part_blueprint
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        if gable_blueprint == 'NONE':
            gables = spawn_empty_base(tile_props)
        elif gable_blueprint == 'PLAIN':
            gables = spawn_base(self, tile_props)

        if rooftop_blueprint == 'NONE':
            rooftop = None
        else:
            rooftop = spawn_roof(self, tile_props)
        self.finalise_tile(context, gables, rooftop)

    def execute(self, context):
        """Execute the Operator."""
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

        layout.label(text="Roof Type")
        layout.prop(self, 'roof_type', text="")
        layout.prop(self, 'base_blueprint', text="Gable")
        layout.prop(self, 'main_part_blueprint', text="Rooftop")
        '''
        row = layout.row()
        row.prop(self, 'draw_gables')
        row.prop(self, 'draw_rooftop')
        '''
        layout.label(text="Materials")
        if self.base_blueprint != "NONE":
            layout.prop(self, 'gable_material')
        if self.main_part_blueprint != "NONE":
            layout.prop(self, 'rooftop_material')

        # layout.label(text="Socket Types")
        layout.label(text="Bottom Socket")
        layout.prop(self, 'base_bottom_socket_type', text="")
        # layout.prop(roof_props, 'base_side_socket_type')
        # layout.prop(roof_props, 'gable_socket_type')
        layout.prop(scene_props, 'generate_suppports')

        layout.label(text="Roof Footprint")
        row = layout.row()
        row.prop(self, 'base_x')
        row.prop(self, 'base_y')

        layout.label(text="Roof Properties")

        layout.prop(self, 'roof_pitch', text="Roof Pitch")
        layout.prop(self, 'end_eaves_pos', text="Positive End Eaves")
        layout.prop(self, 'end_eaves_neg', text="Negative End Eaves")
        layout.prop(self, 'roof_thickness')

        layout.prop(self, 'side_eaves', text="Side Eaves")
        layout.prop(self, 'base_z', text="Base Height")

        layout.label(text="Wall Inset Correction")
        layout.prop(self, 'inset_dist', text="Inset Distance")
        row = layout.row()
        row.prop(self, 'inset_x_neg', text="X Neg")
        row.prop(self, 'inset_x_pos', text="X Pos")
        row.prop(self, 'inset_y_neg', text="Y Neg")
        row.prop(self, 'inset_y_pos', text="Y Pos")

        layout.label(text="UV Island Margin")
        layout.prop(self, 'UV_island_margin', text="")


class MT_OT_Make_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof Base."""

    bl_idname = "object.make_plain_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        # roof_props = context.collection.mt_roof_tile_props
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_base(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty roof base."""

    bl_idname = "object.make_empty_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_empty_base(tile_props)
        return{'FINISHED'}


class MT_OT_Make_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an openlock Roof Top."""

    bl_idname = "object.make_openlock_roof_top"
    bl_label = "Roof Top"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        tile_props = bpy.data.collections[self.tile_name].mt_tile_props
        spawn_roof(self, tile_props)
        return{'FINISHED'}


class MT_OT_Make_Empty_Roof_Top(MT_Tile_Generator, Operator):
    """Internal Operator. Generate an empty roof top."""

    bl_idname = "object.make_empty_roof_top"
    bl_label = "Roof Gable"
    bl_options = {'INTERNAL'}
    mt_blueprint = "NONE"
    mt_type = "ROOF_TOP"

    def execute(self, context):
        """Execute the operator."""
        return{'PASS_THROUGH'}


def spawn_roof(self, tile_props):
    if tile_props.roof_type == 'APEX':
        roof = draw_apex_roof_top(self, tile_props)
    elif tile_props.roof_type == 'SHED':
        roof = draw_shed_roof_top(self, tile_props)
    elif tile_props.roof_type == 'BUTTERFLY':
        roof = draw_butterfly_roof_top(self, tile_props)

    roof.name = tile_props.tile_name + '.roof'
    obj_props = roof.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    bpy.context.scene.cursor.location = (0, 0, 0)
    subsurf = add_subsurf_modifier(roof)
    textured_vertex_groups = ['Left', 'Right']
    material = tile_props.rooftop_material

    convert_to_displacement_core(
        roof,
        textured_vertex_groups,
        material,
        subsurf)
    return roof


# @profile
def spawn_base(self, tile_props):
    if tile_props.roof_type == 'APEX':
        base = draw_apex_base(self, tile_props)
    elif tile_props.roof_type == 'SHED':
        base = draw_shed_base(self, tile_props)
    elif tile_props.roof_type == 'BUTTERFLY':
        base = draw_butterfly_base(self, tile_props)

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    bpy.context.scene.cursor.location = (0, 0, 0)
    subsurf = add_subsurf_modifier(base)

    if tile_props.base_bottom_socket_type == 'OPENLOCK':
        slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props)
        set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
        set_bool_props(slot_cutter, base, 'DIFFERENCE')

    textured_vertex_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back']
    material = tile_props.gable_material

    convert_to_displacement_core(
        base,
        textured_vertex_groups,
        material,
        subsurf)

    activate(base.name)
    return base


# @profile
def spawn_openlock_base_slot_cutter(base, tile_props, offset=0.236):
    """Spawn an openlock base slot cutter into scene and positions it correctly.

    Args:
        base (bpy.types.Object): base
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.type.Object: slot cutter
    """

    base_location = base.location.copy()
    base_dims = base.dimensions.copy()

    # correct for wall inset distance
    if tile_props.inset_x_neg:
        base_dims[0] = base_dims[0] + tile_props.inset_dist
    if tile_props.inset_x_pos:
        base_dims[0] = base_dims[0] + tile_props.inset_dist
    if tile_props.inset_y_neg:
        base_dims[1] = base_dims[1] + tile_props.inset_dist
    if tile_props.inset_y_pos:
        base_dims[1] = base_dims[1] + tile_props.inset_dist

    # one sided base socket
    if base_dims[0] <= 1 or base_dims[1] <= 1:
        # work out bool size X from base size, y and z are constants.
        bool_size = [
            base_dims[0] - (offset * 2),
            0.145,
            0.25]

        cutter = draw_cuboid(bool_size)
        cutter.name = 'Base Slot.' + tile_props.tile_name + ".slot_cutter"

        diff = base_dims[0] - bool_size[0]

        cutter.location = (
            base_location[0] + diff / 2,
            base_location[1] + offset,
            base_location[2] - 0.001)

        return cutter

    # 4 sided base socket
    else:
        preferences = get_prefs()
        booleans_path = os.path.join(
            preferences.assets_path,
            "meshes",
            "booleans",
            "rect_floor_slot_cutter.blend")

        with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
            data_to.objects = [
                'corner_xneg_yneg',
                'corner_xneg_ypos',
                'corner_xpos_yneg',
                'corner_xpos_ypos',
                'slot_cutter_a',
                'slot_cutter_b',
                'slot_cutter_c',
                'base_slot_cutter_final']

        for obj in data_to.objects:
            add_object_to_collection(obj, tile_props.tile_name)

        for obj in data_to.objects:
            # obj.hide_set(True)
            obj.hide_viewport = True

        cutter_a = data_to.objects[4]
        cutter_b = data_to.objects[5]
        cutter_c = data_to.objects[6]
        cutter_d = data_to.objects[7]

        cutter_d.name = 'Base Slot Cutter.' + tile_props.tile_name

        a_array = cutter_a.modifiers['Array']
        a_array.fit_length = base_dims[1] - 1.014

        b_array = cutter_b.modifiers['Array']
        b_array.fit_length = base_dims[0] - 1.014

        c_array = cutter_c.modifiers['Array']
        c_array.fit_length = base_dims[0] - 1.014

        d_array = cutter_d.modifiers['Array']
        d_array.fit_length = base_dims[1] - 1.014

        cutter_d.location = (
            base_location[0] + 0.24,
            base_location[1] + 0.24,
            base_location[2] + 0.24)

        return cutter_d
