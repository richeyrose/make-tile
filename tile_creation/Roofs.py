import bpy

from bpy.types import Operator, Panel
from .. lib.utils.collections import (
    create_collection,
    activate_collection)

from .. lib.utils.utils import mode, get_all_subclasses
from ..lib.utils.selection import activate
from .create_tile import (
    finalise_tile,
    spawn_empty_base,
    convert_to_displacement_core,
    spawn_prefab,
    set_bool_obj_props,
    set_bool_props,
    MT_Tile_Generator,
    initialise_tile_creator,
    create_common_tile_props)

from .apex_roof import draw_apex_roof_top, draw_apex_base
from .Rectangular_Tiles import spawn_openlock_base_slot_cutter

# TODO Make side eaves seperately customisable in same way as end eaves
# TODO Ensure UI updates to show roof options when roof is selected
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
        roof_props = scene.mt_roof_scene_props

        layout = self.layout

        # layout.label(text="Blueprints")
        layout.label(text="Roof Type")
        layout.prop(roof_props, 'roof_type', text="")

        row = layout.row()
        row.prop(roof_props, 'draw_gables')
        row.prop(roof_props, 'draw_rooftop')

        # layout.label(text="Socket Types")
        layout.label(text="Bottom Socket")
        layout.prop(roof_props, 'base_bottom_socket_type', text="")
        # layout.prop(roof_props, 'base_side_socket_type')
        # layout.prop(roof_props, 'gable_socket_type')

        layout.label(text="Roof Footprint")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')

        layout.label(text="Roof Properties")

        layout.prop(roof_props, 'roof_pitch', text="Roof Pitch")
        layout.prop(roof_props, 'end_eaves_pos', text="Positive End Eaves")
        layout.prop(roof_props, 'end_eaves_neg', text="Negative End Eaves")
        layout.prop(roof_props, 'roof_thickness')

        layout.prop(roof_props, 'side_eaves', text="Side Eaves")
        layout.prop(scene_props, 'base_z', text="Base Height")

        layout.label(text="Subdivision Density")
        layout.prop(scene_props, 'subdivision_density', text="")

        layout.label(text="Wall Inset Correction")
        layout.prop(roof_props, 'inset_dist', text="Inset Distance")
        row = layout.row()
        row.prop(roof_props, 'inset_x_neg', text="X Neg")
        row.prop(roof_props, 'inset_x_pos', text="X Pos")
        row.prop(roof_props, 'inset_y_neg', text="Y Neg")
        row.prop(roof_props, 'inset_y_pos', text="Y Pos")

        layout.operator('scene.reset_roof_defaults')

def initialise_roof_creator(context):
    """Initialise the roof creator and set common properties."""
    tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot = initialise_tile_creator(context)
    create_collection('Roofs', tiles_collection)
    tile_collection = bpy.data.collections.new(tile_name)
    bpy.data.collections['Roofs'].children.link(tile_collection)
    activate_collection(tile_collection.name)

    tile_props = tile_collection.mt_tile_props
    roof_tile_props = tile_collection.mt_roof_tile_props

    scene_props = context.scene.mt_scene_props
    roof_scene_props = context.scene.mt_roof_scene_props
    create_common_tile_props(scene_props, tile_props, tile_collection)
    create_roof_tile_props(roof_scene_props, roof_tile_props)

    roof_tile_props.is_roof = True

    tile_props.tile_size = (scene_props.tile_x, scene_props.tile_y, scene_props.tile_z)
    tile_props.base_size = (scene_props.base_x, scene_props.base_y, scene_props.base_z)
    tile_props.tile_type = 'ROOF'

    return cursor_orig_loc, cursor_orig_rot

def create_roof_tile_props(roof_scene_props, roof_tile_props):
    """Create roof tile properties.

    Args:
        roof_scene_props (MakeTile.properties.MT_Roof_Properties): scene props
        roof_tile_props (MakeTile.properties.MT_Roof_Properties): tile props
    """
    for key in roof_scene_props.__annotations__.keys():
        for k in roof_tile_props.__annotations__.keys():
            if k == key:
                setattr(roof_tile_props, str(k), getattr(roof_scene_props, str(k)))

class MT_OT_Make_Roof(MT_Tile_Generator, Operator):
    """Operator. Generates a roof tile."""

    bl_idname = "object.make_roof"
    bl_label = "Roof"
    bl_options = {'UNDO'}
    mt_blueprint = "CUSTOM"
    mt_type = "ROOF"

    def execute(self, context):
        """Execute the Operator."""
        scene = context.scene
        roof_scene_props = scene.mt_roof_scene_props
        cursor_orig_loc, cursor_orig_rot = initialise_roof_creator(
            context)
        subclasses = get_all_subclasses(MT_Tile_Generator)

        if roof_scene_props.draw_gables:
            gable_type = 'PLAIN'
        else:
            gable_type = 'NONE'

        if roof_scene_props.draw_rooftop:
            rooftop_type = 'PLAIN'
            rooftop = spawn_prefab(context, subclasses, rooftop_type, 'ROOF_TOP')
        else:
            rooftop = None

        gables = spawn_prefab(context, subclasses, gable_type, 'ROOF_BASE')

        finalise_tile(gables, rooftop, cursor_orig_loc, cursor_orig_rot)

        return {'FINISHED'}

class MT_OT_Make_Roof_Base(MT_Tile_Generator, Operator):
    """Internal Operator. Generate a Roof Base."""

    bl_idname = "object.make_plain_roof_base"
    bl_label = "Roof Base"
    bl_options = {'INTERNAL'}
    mt_blueprint = "PLAIN"
    mt_type = "ROOF_BASE"

    def execute(self, context):
        """Execute the operator."""
        roof_props = context.collection.mt_roof_tile_props
        tile_props = context.collection.mt_tile_props

        base = spawn_base(self, context)

        if roof_props.base_bottom_socket_type == 'OPENLOCK':
            slot_cutter = spawn_openlock_base_slot_cutter(base, tile_props, roof_props)
            set_bool_obj_props(slot_cutter, base, tile_props, 'DIFFERENCE')
            set_bool_props(slot_cutter, base, 'DIFFERENCE')

        textured_vertex_groups = ['Base Left', 'Base Right', 'Gable Front', 'Gable Back']
        convert_to_displacement_core(
            base,
            textured_vertex_groups)

        activate(base.name)
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
        roof = spawn_roof(self, context)
        textured_vertex_groups = ['Left', 'Right']
        convert_to_displacement_core(
            roof,
            textured_vertex_groups)
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
        tile = context.collection
        tile_props = tile.mt_tile_props
        spawn_empty_base(tile_props)
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

def spawn_roof(self, context):
    tile = context.collection
    tile_props = tile.mt_tile_props
    roof_props = tile.mt_roof_tile_props

    if roof_props.roof_type == 'APEX':
        roof = draw_apex_roof_top(self, context)
    elif roof_props.roof_type == 'SHED':
        roof = draw_shed_roof_top(context)
    elif roof_props.roof_type == 'BUTTERFLY':
        roof = draw_butterfly_roof_top(context)

    roof.name = tile_props.tile_name + '.roof'
    obj_props = roof.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': roof,
        'active_object': roof,
        'selected_objects': [roof],
        'selected_editable_objects': [roof]}

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')
    return roof


def spawn_base(self, context):
    tile = context.collection
    tile_props = tile.mt_tile_props
    roof_props = tile.mt_roof_tile_props

    if roof_props.roof_type == 'APEX':
        base = draw_apex_base(self, context)
    elif roof_props.roof_type == 'SHED':
        base = draw_shed_base(context)
    elif roof_props.roof_type == 'BUTTERFLY':
        base = draw_butterfly_base(context)

    base.name = tile_props.tile_name + '.base'
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name

    ctx = {
        'object': base,
        'active_object': base,
        'selected_objects': [base],
        'selected_editable_objects': [base]}

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    return base
