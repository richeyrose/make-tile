import bpy
from bpy.types import PropertyGroup
from ..tile_creation.create_tile import MT_Tile_Generator
from ..lib.utils.utils import get_all_subclasses


# Radio buttons used in menus
class MT_Radio_Buttons(PropertyGroup):
    def update_mapping_axis(self, context):
        axis = context.window_manager.mt_radio_buttons.mapping_axis
        material = context.object.active_material
        tree = material.node_tree
        nodes = tree.nodes
        axis_node = nodes['Wrap Around Axis']

        if axis == 'X':
            axis_node.inputs[0].default_value = 1
            axis_node.inputs[1].default_value = 0
            axis_node.inputs[2].default_value = 0
        elif axis == 'Y':
            axis_node.inputs[0].default_value = 0
            axis_node.inputs[1].default_value = 1
            axis_node.inputs[2].default_value = 0
        elif axis == 'Z':
            axis_node.inputs[0].default_value = 0
            axis_node.inputs[1].default_value = 0
            axis_node.inputs[2].default_value = 1

    mapping_axis: bpy.props.EnumProperty(
        items=[
            ('X', 'X', 'X', '', 0),
            ('Y', 'Y', 'Y', '', 1),
            ('Z', 'Z', 'Z', '', 2)
        ],
        default='Z',
        description='Mapping axis for wrap around material projection',
        update=update_mapping_axis
    )


def create_tile_type_enums(self, context):
    """Create an enum of tile types out of subclasses of MT_OT_Make_Tile."""
    enum_items = []
    if context is None:
        return enum_items

    # blueprint = context.scene.mt_scene_props.tile_blueprint
    subclasses = get_all_subclasses(MT_Tile_Generator)

    for subclass in subclasses:
        # if hasattr(subclass, 'mt_blueprint'):
        if 'INTERNAL' not in subclass.bl_options:
            enum = (subclass.mt_type, subclass.bl_label, "")
            enum_items.append(enum)
    return sorted(enum_items)


def create_main_part_blueprint_enums(self, context):
    """Dynamically creates a list of enum items depending on what is set in the tile_type defaults.

    Args:
        context (bpy.Context): scene context

    Returns:
        list[enum_item]: list of enum items
    """
    enum_items = []
    scene = context.scene
    scene_props = scene.mt_scene_props

    if context is None:
        return enum_items

    if 'tile_defaults' not in scene_props:
        return enum_items

    tile_type = scene_props.tile_type
    tile_defaults = scene_props['tile_defaults']

    for default in tile_defaults:
        if default['type'] == tile_type:
            for key, value in default['main_part_blueprints'].items():
                enum = (key, value, "")
                enum_items.append(enum)
            return sorted(enum_items)
    return enum_items


def create_base_blueprint_enums(self, context):
    enum_items = []
    scene = context.scene
    scene_props = scene.mt_scene_props

    if context is None:
        return enum_items

    if 'tile_defaults' not in scene_props:
        return enum_items

    tile_type = scene_props.tile_type
    tile_defaults = scene_props['tile_defaults']

    for default in tile_defaults:
        if default['type'] == tile_type:
            for key, value in default['base_blueprints'].items():
                enum = (key, value, "")
                enum_items.append(enum)
            return sorted(enum_items)
    return enum_items


def update_tile_blueprint(self, context):
    blueprint = context.scene.mt_scene_props.tile_blueprint
    subclasses = get_all_subclasses(MT_Tile_Generator)

    for subclass in subclasses:
        if hasattr(subclass, 'mt_blueprint'):
            if subclass.mt_blueprint == blueprint and 'INTERNAL' not in subclass.bl_options:
                context.scene.mt_scene_props.tile_type = subclass.bl_idname
                break


def register():
    bpy.types.WindowManager.mt_radio_buttons = bpy.props.PointerProperty(
        type=MT_Radio_Buttons
    )


def unregister():
    del bpy.types.WindowManager.mt_radio_buttons
