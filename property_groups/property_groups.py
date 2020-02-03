import bpy
from bpy.types import PropertyGroup

from .. enums.enums import (
    tile_main_systems,
    tile_types,
    base_systems,
    tile_blueprints,
    curve_types,
    geometry_types,
    base_socket_side)


# Radio buttons used in menus
class MT_Radio_Buttons(PropertyGroup):
    def update_mapping_axis(self, context):
        axis = context.window_manager.mt_radio_buttons.mapping_axis
        material = bpy.data.materials[context.scene.mt_tile_material_1]
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


# A cutter item used by mt_cutters_collection and mt_trimmers_collection
class MT_Cutter_Item(PropertyGroup):
    def update_use_cutter(self, context):
        if self.parent is not "":
            parent_obj = bpy.data.objects[self.parent]
            bool_mod = parent_obj.modifiers[self.name + '.bool']
            bool_mod.show_viewport = self.value

            if parent_obj.mt_object_props.linked_object is not None:
                linked_obj = parent_obj.mt_object_props.linked_object
                bool_mod = linked_obj.modifiers[self.name + '.bool']
                bool_mod.show_viewport = self.value

    name: bpy.props.StringProperty(
        name="Cutter Name")
    value: bpy.props.BoolProperty(
        name="",
        default=True,
        update=update_use_cutter)
    parent: bpy.props.StringProperty(
        name="")


class MT_Trimmer_Item(PropertyGroup):
    def update_use_trimmer(self, context):
        obj = context.object
        if self.name + '.bool' in obj.modifiers:
            bool_mod = obj.modifiers[self.name + '.bool']
            bool_mod.show_viewport = self.value

    name: bpy.props.StringProperty(
        name="Trimmer Name")
    value: bpy.props.BoolProperty(
        name="",
        default=False,
        update=update_use_trimmer)
    parent: bpy.props.StringProperty(
        name="")


class MT_Disp_Mat_Item(PropertyGroup):
    material: bpy.props.PointerProperty(
        name="Displacement Material",
        type=bpy.types.Material
    )


class MT_Object_Properties(PropertyGroup):
    is_mt_object: bpy.props.BoolProperty(
        name="Is MakeTile Object",
        default=False
    )

    tile_name: bpy.props.StringProperty(
        name="Tile Name"
    )

    geometry_type: bpy.props.EnumProperty(
        name="Geometry Type",
        items=geometry_types
    )

    # Collection of cutters that can be turned on or off
    # by MakeTile.
    cutters_collection: bpy.props.CollectionProperty(
        name="Cutters Collection",
        type=MT_Cutter_Item
    )

    linked_object: bpy.props.PointerProperty(
        name="Linked Object",
        type=bpy.types.Object,
        description="Used for storing a reference from a preview object to a displacement object and vice versa"
    )

    disp_materials_collection: bpy.props.CollectionProperty(
        name="Displacement materials collection",
        type=MT_Disp_Mat_Item
    )


class MT_Tile_Properties(PropertyGroup):
    is_mt_collection: bpy.props.BoolProperty(
        name="Is MakeTile collection",
        default=False)

    tile_name: bpy.props.StringProperty(
        name="Tile Name"
    )

    tile_blueprint: bpy.props.EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        description="Blueprint for entire tile - e.g. openLOCK or Plain")

    main_part_blueprint: bpy.props.EnumProperty(
        items=tile_main_systems,
        name="Main System",
        description="Blueprint for main part of tile. \
        #  E.g. for a wall this would be the system used for the \
        #vertical bit")

    base_blueprint: bpy.props.EnumProperty(
        items=base_systems,
        name="Base System",
        description="Blueprint for base of the tile.")

    tile_type: bpy.props.EnumProperty(
        items=tile_types,
        name="Type",
        description="The type of tile e.g. Straight Wall, Curved Floor",
        default="STRAIGHT_WALL",
    )

    tile_size: bpy.props.FloatVectorProperty(
        name="Tile Size"
    )

    base_size: bpy.props.FloatVectorProperty(
        name="Base size"
    )

    base_radius: bpy.props.FloatProperty(
        name="Base Radius"
    )

    wall_radius: bpy.props.FloatProperty(
        name="Wall Radius"
    )
    
    base_socket_side: bpy.props.EnumProperty(
        name="Socket Side",
        items=base_socket_side
    )

    degrees_of_arc: bpy.props.FloatProperty(
        name="Degrees of Arc"
    )

    angle: bpy.props.FloatProperty(
        name="Angle"
    )

    segments: bpy.props.IntProperty(
        name="Segments"
    )

    leg_1_len: bpy.props.FloatProperty(
        name="Leg 1 Length"
    )

    leg_2_len: bpy.props.FloatProperty(
        name="Leg 2 Length"
    )

    curve_type: bpy.props.EnumProperty(
        name="Curve Type",
        items=curve_types
    )
    # Collection of trimmers that can be turned on or off
    # by MakeTile. Deprecated
    trimmers_collection: bpy.props.CollectionProperty(
        type=MT_Trimmer_Item
    )
