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
