import os
import bpy
from bpy.types import PropertyGroup
from .. utils.registration import get_prefs

from .. enums.enums import (
    tile_main_systems,
    tile_types,
    base_systems,
    tile_blueprints,
    curve_types,
    geometry_types,
    base_socket_side,
    units,
    material_mapping)

from .. materials.materials import (
    get_blend_filenames,
    load_materials)

from .. lib.utils.update_scene_props import load_material_libraries

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

class MT_Scene_Properties(PropertyGroup):
    def change_tile_type(self, context):
        self.update_size_defaults(context)
        self.update_subdiv_defaults(context)
    
    def update_size_defaults(self, context):
        '''updates tile and base size defaults depending on whether we are generating a base or wall'''
        scene_props = context.scene.mt_scene_props
        if scene_props.mt_tile_type in (
                'RECTANGULAR_FLOOR', 
                'TRIANGULAR_FLOOR',
                'CURVED_FLOOR',
                'CORNER_FLOOR',
                'STRAIGHT_FLOOR',
                'SEMI_CIRC_FLOOR'):
            scene_props.mt_tile_z = 0.3
            scene_props.mt_base_z = 0.2755
            scene_props.mt_tile_x = 2
            scene_props.mt_tile_y = 2
            scene_props.mt_base_x = 2
            scene_props.mt_base_y = 2
        else:
            scene_props.mt_tile_z = 2
            scene_props.mt_base_z = 0.2755
            scene_props.mt_base_y = 0.5
            scene_props.mt_tile_y = 0.3149


    def update_subdiv_defaults(self, context):
        scene_props = context.scene.mt_scene_props
        if scene_props.mt_tile_type in (
                'STRAIGHT_WALL',
                'CURVED_WALL',
                'CORNER_WALL'):
            scene_props.mt_native_subdivisions = (15, 2, 15)
        elif scene_props.mt_tile_type in (
                'STRAIGHT_FLOOR',
                'CURVED_FLOOR',
                'CORNER_FLOOR'):
            scene_props.mt_native_subdivisions = (15, 3, 1)
        elif scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR' and scene_props.mt_curve_type == 'NEG':
            scene_props.mt_native_subdivisions = (15, 8, 1)
            scene_props.mt_segments = 20
        elif scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR' and scene_props.mt_curve_type == 'POS':
            scene_props.mt_native_subdivisions = (15, 15, 1)
            scene_props.mt_segments = 20
        else:
            scene_props.mt_native_subdivisions = (15, 15, 1)

    def update_disp_strength(self, context):
        obj = bpy.context.object
        obj_props = obj.mt_object_props
        tile = bpy.data.collections[obj_props.tile_name]
        tile.mt_tile_props.displacement_strength = context.scene.mt_scene_props.mt_displacement_strength
        if obj_props.geometry_type == 'DISPLACEMENT':
            if 'Displacement' in obj.modifiers:
                mod = obj.modifiers['Displacement']
                mod.strength = context.scene.mt_scene_props.mt_displacement_strength

    def update_disp_subdivisions(self, context):
        '''Updates the numnber of subdivisions used by the displacement material modifier'''
        obj = bpy.context.object
        obj_props = obj.mt_object_props
        if obj_props.geometry_type == 'DISPLACEMENT':
            if 'Subsurf' in obj.modifiers:
                modifier = obj.modifiers['Subsurf']
                modifier.levels = context.scene.mt_scene_props.mt_subdivisions

    def update_material_mapping(self, context):
        '''updates which mapping method to use for a material'''
        material = context.object.active_material
        tree = material.node_tree
        nodes = tree.nodes

        map_meth = context.scene.mt_scene_props.mt_material_mapping_method

        if 'master_mapping' in nodes:
            mapping_node = nodes['master_mapping']
            if map_meth == 'WRAP_AROUND':
                map_type_node = nodes['wrap_around_map']
                tree.links.new(
                    map_type_node.outputs['Vector'],
                    mapping_node.inputs['Vector'])
            elif map_meth == 'TRIPLANAR':
                map_type_node = nodes['triplanar_map']
                tree.links.new(
                    map_type_node.outputs['Vector'],
                    mapping_node.inputs['Vector'])
            elif map_meth == 'OBJECT':
                map_type_node = nodes['object_map']
                tree.links.new(
                    map_type_node.outputs['Color'],
                    mapping_node.inputs['Vector'])
            elif map_meth == 'GENERATED':
                map_type_node = nodes['generated_map']
                tree.links.new(
                    map_type_node.outputs['Color'],
                    mapping_node.inputs['Vector'])
            elif map_meth == 'UV':
                map_type_node = nodes['UV_map']
                tree.links.new(
                    map_type_node.outputs['Color'],
                    mapping_node.inputs['Vector'])

    def load_material_enums(self, context):
        '''Constructs a material Enum from materials found in the materials asset folder'''
        enum_items = []    
        if context is None:
            return enum_items

        if context.scene.mt_scene_props.mt_is_just_activated is True:
            load_material_libraries(dummy=None)
            #context.scene.mt_scene_props.mt_is_just_activated = False

        prefs = get_prefs()

        materials = bpy.data.materials
        for material in materials:
            # prevent make-tile adding the default material to the list
            if material.name != prefs.secondary_material and material.name != 'Material':
                enum = (material.name, material.name, "")
                enum_items.append(enum)
        return enum_items

    # TODO: See why we get warning if we use this
    def get_default_units(self, context):
        prefs = get_prefs()
        return prefs.default_units

    def get_default_tile_blueprint(self, context):
        prefs = get_prefs()
        return prefs.default_tile_blueprint

    def get_default_tile_main_system(self, context):
        prefs = get_prefs()
        return prefs.default_tile_main_system

    def get_default_base_system(self, context):
        prefs = get_prefs()
        return prefs.default_base_system

    mt_native_subdivisions: bpy.props.IntVectorProperty(
        name="Native Subdivisions",
        description="The number of times to subdivide the tile on creation",
        min=1,
        soft_max=25,
        default=(15, 2, 15),
        subtype='XYZ'
    )

    mt_is_just_activated: bpy.props.BoolProperty(
        description="Has the add-on just been activated. Used to populate materials list first time round",
        default=False
    )

    mt_last_selected: bpy.props.PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object
    )

    mt_tile_name: bpy.props.StringProperty(
        name="Tile Name",
        default="Tile"
    )

    mt_tile_units: bpy.props.EnumProperty(
        items=units,
        name="Units",
        default='INCHES'
    )

    mt_tile_blueprint: bpy.props.EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        default='OPENLOCK'
    )

    mt_main_part_blueprint: bpy.props.EnumProperty(
        items=tile_main_systems,
        name="Main System",
        default='OPENLOCK'
    )

    mt_tile_type: bpy.props.EnumProperty(
        items=tile_types,
        name="Type",
        default="STRAIGHT_WALL",
        update=change_tile_type
    )

    mt_base_blueprint: bpy.props.EnumProperty(
        items=base_systems,
        name="Base Type",
        default='OPENLOCK'
    )

    mt_material_mapping_method: bpy.props.EnumProperty(
        items=material_mapping,
        description="How to map the active material onto an object",
        name="Material Mapping Method",
        update=update_material_mapping,
        default='OBJECT'
    )

    mt_displacement_strength: bpy.props.FloatProperty(
        name="Displacement Strength",
        description="Overall Displacement Strength",
        default=0.1,
        step=1,
        precision=3,
        update=update_disp_strength
    )

    mt_tile_material_1: bpy.props.EnumProperty(
        items=load_material_enums,
        name="Material"
    )

    mt_tile_resolution: bpy.props.IntProperty(
        name="Resolution",
        description="Bake resolution of displacement maps. Higher = better quality but slower. Also images are 32 bit so 4K and 8K images can be gigabytes in size",
        default=1024,
        min=1024,
        max=8192,
        step=1024,
    )
    
    mt_subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        description="How many times to subdivide the displacement mesh. Higher = better but slower. \
        Going above 8 is really not recommended and may cause Blender to freeze up for a loooooong time!",
        default=4,
        soft_max=8,
        update=update_disp_subdivisions
    )

    # Tile and base size. We use seperate floats so that we can only show
    # customisable ones where appropriate. These are wrapped up
    # in a vector and passed on as tile_size and base_size

    # Tile size
    mt_tile_x: bpy.props.FloatProperty(
        name="X",
        default=2.0,
        step=0.5,
        precision=3,
        min=0
    )

    mt_tile_y: bpy.props.FloatProperty(
        name="Y",
        default=2,
        step=0.5,
        precision=3,
        min=0
    )

    mt_tile_z: bpy.props.FloatProperty(
        name="Z",
        default=2.0,
        step=0.1,
        precision=3,
        min=0
    )

    # Base size
    mt_base_x: bpy.props.FloatProperty(
        name="X",
        default=2.0,
        step=0.5,
        precision=3,
        min=0
    )

    mt_base_y: bpy.props.FloatProperty(
        name="Y",
        default=0.5,
        step=0.5,
        precision=3,
        min=0
    )

    mt_base_z: bpy.props.FloatProperty(
        name="Z",
        default=0.3,
        step=0.1,
        precision=3,
        min=0
    )

    # Corner wall and triangular base specific
    mt_angle: bpy.props.FloatProperty(
        name="Base Angle",
        default=90,
        step=5,
        precision=1
    )

    mt_leg_1_len: bpy.props.FloatProperty(
        name="Leg 1 Length",
        description="Length of leg",
        default=2,
        step=0.5,
        precision=2
    )

    mt_leg_2_len: bpy.props.FloatProperty(
        name="Leg 2 Length",
        description="Length of leg",
        default=2,
        step=0.5,
        precision=2
    )

    # Openlock curved wall specific
    mt_base_socket_side: bpy.props.EnumProperty(
        items=base_socket_side,
        name="Socket Side",
        default="INNER",
    )

    # Used for curved wall tiles
    mt_base_radius: bpy.props.FloatProperty(
        name="Base inner radius",
        default=2.0,
        step=0.5,
        precision=3,
        min=0,
    )

    mt_wall_radius: bpy.props.FloatProperty(
        name="Wall inner radius",
        default=2.0,
        step=0.5,
        precision=3,
        min=0
    )

    # used for curved floors
    mt_curve_type: bpy.props.EnumProperty(
        items=curve_types,
        name="Curve type",
        default="POS",
        description="Whether the tile has a positive or negative curvature"
    )

    # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
    mt_degrees_of_arc: bpy.props.FloatProperty(
        name="Degrees of arc",
        default=90,
        step=45,
        precision=1,
        max=359.999,
        min=0
    )

    mt_segments: bpy.props.IntProperty(
        name="Number of segments",
        default=20
    )

    '''
    @classmethod
    def unregister(cls):
        for pcoll in enum_collections.values():
            bpy.utils.previews.remove(pcoll)
        enum_collections.clear()
    '''


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

    tile_native_subdivisions: bpy.props.IntVectorProperty(
        name="Native Subdivisions",
        description="The number of times to subdivide the tile on creation",
        default=(15, 2, 15)
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

    tile_units: bpy.props.EnumProperty(
        name="Tile Units",
        items=units
    )

    displacement_strength: bpy.props.FloatProperty(
        name="Displacement Strength"
    )

    tile_resolution: bpy.props.IntProperty(
        name="Tile Resolution"
    )

    subdivisions: bpy.props.IntProperty(
        name="Subdivisions"
    )

    # Collection of trimmers that can be turned on or off
    # by MakeTile. Deprecated
    trimmers_collection: bpy.props.CollectionProperty(
        type=MT_Trimmer_Item
    )
