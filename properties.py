import os
import bpy
from bpy.types import PropertyGroup
from .utils.registration import get_prefs
from .operators.maketile import MT_Tile_Generator
from . enums.enums import (
    tile_main_systems,
    base_systems,
    tile_blueprints,
    curve_types,
    geometry_types,
    base_socket_side,
    units,
    material_mapping,
    openlock_column_types)

from .app_handlers import load_material_libraries
from .lib.utils.utils import get_all_subclasses


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


# A cutter item used by cutters_collection
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


def update_scene_defaults(self, context):
    scene_props = context.scene.mt_scene_props
    tile_type = scene_props.tile_type
    tile_defaults = scene_props['tile_defaults']

    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            for key, value in defaults.items():
                setattr(scene_props, key, value)
            break

    update_main_part_defaults(self, context)
    update_base_defaults(self, context)


def update_base_defaults(self, context):
    scene_props = context.scene.mt_scene_props
    tile_type = scene_props.tile_type
    base_blueprint = scene_props.base_blueprint
    tile_defaults = scene_props['tile_defaults']

    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            base_defaults = defaults['base_defaults']
            for key, value in base_defaults.items():
                if key == base_blueprint:
                    for k, v in value.items():
                        setattr(scene_props, k, v)
                    break


def update_main_part_defaults(self, context):
    scene_props = context.scene.mt_scene_props
    tile_type = scene_props.tile_type
    main_part_blueprint = scene_props.main_part_blueprint
    tile_defaults = scene_props['tile_defaults']

    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            main_part_defaults = defaults['tile_defaults']
            for key, value in main_part_defaults.items():
                if key == main_part_blueprint:
                    for k, v in value.items():
                        setattr(scene_props, k, v)
                    break


def load_material_enums(self, context):
    '''Constructs a material Enum from materials found in the materials asset folder'''
    enum_items = []
    if context is None:
        return enum_items

    if context.scene.mt_scene_props.mt_is_just_activated is True:
        load_material_libraries(dummy=None)

    prefs = get_prefs()

    materials = bpy.data.materials
    for material in materials:
        # prevent make-tile adding the default material to the list
        if material.name != prefs.secondary_material and material.name != 'Material':
            enum = (material.name, material.name, "")
            enum_items.append(enum)
    return enum_items


def update_base_x(self, context):
    """Update the x dimension of the base based on the size of the tile.

    Args:
        context (bpy.context): scene context
    """
    scene_props = context.scene.mt_scene_props
    tile_x = scene_props.tile_x
    base_x = scene_props.base_x
    proportionate = scene_props.x_proportionate_scale

    if proportionate:
        scene_props.base_x = base_x + (tile_x - base_x)

def update_base_y(self, context):
    """Update the y dimension of the base based on the size of the tile.

    Args:
        context (bpy.context): scene context
    """
    scene_props = context.scene.mt_scene_props
    tile_y = scene_props.tile_y
    base_y = scene_props.base_y
    proportionate = scene_props.y_proportionate_scale

    if proportionate:
        scene_props.base_y = base_y + (tile_y - base_y)


def update_base_z(self, context):
    """Update the z dimension of the base based on the size of the tile.

    Args:
        context (bpy.context): scene context
    """
    scene_props = context.scene.mt_scene_props
    tile_z = scene_props.tile_z
    base_z = scene_props.base_z
    proportionate = scene_props.z_proportionate_scale

    if proportionate:
        scene_props.base_z = base_z + (tile_z - base_z)


class MT_Scene_Properties(PropertyGroup):
    """Contains MakeTile scene properties.
    Used to store properties that can be set by user for tile generation etc.

    Args:
        PropertyGroup (bpy.types.PropertyGroup): Group of ID properties
    """

    def update_disp_strength(self, context):
        obj = bpy.context.object
        obj_props = obj.mt_object_props
        tile = bpy.data.collections[obj_props.tile_name]
        tile.mt_tile_props.displacement_strength = context.scene.mt_scene_props.displacement_strength
        if obj_props.geometry_type == 'DISPLACEMENT':
            if 'Displacement' in obj.modifiers:
                mod = obj.modifiers['Displacement']
                mod.strength = context.scene.mt_scene_props.displacement_strength

    def update_disp_subdivisions(self, context):
        '''Updates the numnber of subdivisions used by the displacement material modifier'''
        obj = bpy.context.object
        obj_props = obj.mt_object_props
        if obj_props.geometry_type == 'DISPLACEMENT':
            if 'Subsurf' in obj.modifiers:
                modifier = obj.modifiers['Subsurf']
                modifier.levels = context.scene.mt_scene_props.subdivisions

    def update_material_mapping(self, context):
        '''updates which mapping method to use for a material'''
        material = context.object.active_material
        tree = material.node_tree
        nodes = tree.nodes

        map_meth = context.scene.mt_scene_props.material_mapping_method

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

    def update_UV_island_margin(self, context):
        '''Reruns UV smart project for preview and displacement object'''

        if len(bpy.context.selected_editable_objects) > 0:
            obj = bpy.context.object
            if obj.type == 'MESH':
                obj_props = obj.mt_object_props
                if obj_props.geometry_type in ('DISPLACEMENT', 'PREVIEW'):
                    linked_obj = obj_props.linked_object

                    tile = bpy.data.collections[obj_props.tile_name]
                    tile_props = tile.mt_tile_props

                    scene_props = context.scene.mt_scene_props
                    UV_island_margin = scene_props.UV_island_margin
                    tile_props.UV_island_margin = UV_island_margin

                    for ob in (obj, linked_obj):
                        ctx = {
                            'object': ob,
                            'active_object': ob,
                            'selected_objects': [ob]
                        }
                        bpy.ops.uv.smart_project(ctx, island_margin=UV_island_margin)

                    if obj_props.geometry_type == 'DISPLACEMENT':
                        bpy.ops.scene.mt_return_to_preview()
                        bpy.ops.scene.mt_make_3d()

    mt_is_just_activated: bpy.props.BoolProperty(
        description="Has the add-on just been activated. Used to populate materials list first time round",
        default=False
    )

    mt_last_selected: bpy.props.PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object
    )

    tile_name: bpy.props.StringProperty(
        name="Tile Name",
        default="Tile"
    )

    tile_units: bpy.props.EnumProperty(
        items=units,
        name="Units",
        default='INCHES'
    )

    tile_blueprint: bpy.props.EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        default="CUSTOM"
    )

    main_part_blueprint: bpy.props.EnumProperty(
        items=create_main_part_blueprint_enums,
        update=update_main_part_defaults,
        name="Main"
    )

    base_blueprint: bpy.props.EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_defaults,
        name="Base",
    )

    tile_type: bpy.props.EnumProperty(
        items=create_tile_type_enums,
        name="Tile Type",
        update=update_scene_defaults
    )

    UV_island_margin: bpy.props.FloatProperty(
        name="UV Margin",
        default=0.01,
        precision=4,
        min=0,
        step=0.1,
        description="Tweak this if you have gaps in material at edges of tiles when you Make3D",
        update=update_UV_island_margin
    )

    # Native Subdivisions #
    x_native_subdivisions: bpy.props.IntProperty(
        name="X",
        description="The number of times to subdivide the X axis on creation",
        default=15
    )

    y_native_subdivisions: bpy.props.IntProperty(
        name="Y",
        description="The number of times to subdivide the Y axis on creation",
        default=3
    )

    z_native_subdivisions: bpy.props.IntProperty(
        name="Z",
        description="The number of times to subdivide the Z axis on creation",
        default=15
    )

    opposite_native_subdivisions: bpy.props.IntProperty(
        name="Opposite Side",
        description="The number of times to subdivide the edge opposite the root angle on triangular tile creation",
        default=15
    )

    curve_native_subdivisions: bpy.props.IntProperty(
        name="Curved Side",
        description="The number of times to subdivide the curved side of a tile",
        default=15
    )

    leg_1_native_subdivisions: bpy.props.IntProperty(
        name="Leg 1",
        description="The number of times to subdivide the length of leg 1 of the tile",
        default=15
    )

    leg_2_native_subdivisions: bpy.props.IntProperty(
        name="Leg 2",
        description="The number of times to subdivide the length of leg 2 of the tile",
        default=15
    )

    width_native_subdivisions: bpy.props.IntProperty(
        name="Width",
        description="The number of times to subdivide each leg along its width",
        default=3
    )

    material_mapping_method: bpy.props.EnumProperty(
        items=material_mapping,
        description="How to map the active material onto an object",
        name="Material Mapping Method",
        update=update_material_mapping,
        default='OBJECT'
    )

    displacement_strength: bpy.props.FloatProperty(
        name="Displacement Strength",
        description="Overall Displacement Strength",
        default=0.1,
        step=50,
        precision=1,
        update=update_disp_strength
    )

    tile_material_1: bpy.props.EnumProperty(
        items=load_material_enums,
        name="Material"
    )

    tile_resolution: bpy.props.IntProperty(
        name="Resolution",
        description="Bake resolution of displacement maps. Higher = better quality but slower. Also images are 32 bit so 4K and 8K images can be gigabytes in size",
        default=1024,
        min=1024,
        max=8192,
        step=1024,
    )

    subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        description="How many times to subdivide the displacement mesh with a subsurf modifier. Higher = better but slower.",
        default=3,
        soft_max=8,
        update=update_disp_subdivisions
    )

    # Tile and base size. We use seperate floats so that we can only show
    # customisable ones where appropriate. These are wrapped up
    # in a vector and passed on as tile_size and base_size

    # Scale base proportionate to tile
    x_proportionate_scale: bpy.props.BoolProperty(
        name="X",
        default=True
    )

    y_proportionate_scale: bpy.props.BoolProperty(
        name="Y",
        default=False
    )

    z_proportionate_scale: bpy.props.BoolProperty(
        name="Z",
        default=False
    )

    # Tile size
    tile_x: bpy.props.FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=1,
        update=update_base_x,
        min=0
    )

    tile_y: bpy.props.FloatProperty(
        name="Y",
        default=2,
        step=50,
        precision=1,
        update=update_base_y,
        min=0
    )

    tile_z: bpy.props.FloatProperty(
        name="Z",
        default=2.0,
        step=50,
        precision=1,
        update=update_base_z,
        min=0
    )

    # Base size
    base_x: bpy.props.FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=1,
        min=0
    )

    base_y: bpy.props.FloatProperty(
        name="Y",
        default=0.5,
        step=50,
        precision=1,
        min=0
    )

    base_z: bpy.props.FloatProperty(
        name="Z",
        default=0.3,
        step=50,
        precision=1,
        min=0
    )

    # Corner wall and triangular base specific
    angle: bpy.props.FloatProperty(
        name="Base Angle",
        default=90,
        step=5,
        precision=1
    )

    leg_1_len: bpy.props.FloatProperty(
        name="Leg 1 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    leg_2_len: bpy.props.FloatProperty(
        name="Leg 2 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    # Openlock curved wall specific
    base_socket_side: bpy.props.EnumProperty(
        items=base_socket_side,
        name="Socket Side",
        default="INNER",
    )

    # Used for curved wall tiles
    base_radius: bpy.props.FloatProperty(
        name="Base inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0,
    )

    wall_radius: bpy.props.FloatProperty(
        name="Wall inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0
    )

    # used for curved floors
    curve_type: bpy.props.EnumProperty(
        items=curve_types,
        name="Curve type",
        default="POS",
        description="Whether the tile has a positive or negative curvature"
    )

    # Openlock connecting column specific
    openlock_column_type: bpy.props.EnumProperty(
        items=openlock_column_types,
        name="Column type",
        default="O"
    )

    # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
    degrees_of_arc: bpy.props.FloatProperty(
        name="Degrees of arc",
        default=90,
        step=45,
        precision=1,
        max=359.999,
        min=0
    )

    # used for rescaling objects
    base_unit: bpy.props.EnumProperty(
        name="Base Unit",
        items=units
    )

    target_unit: bpy.props.EnumProperty(
        name="Target Unit",
        items=units
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


class MT_Tile_Properties(PropertyGroup):
    is_mt_collection: bpy.props.BoolProperty(
        name="Is MakeTile collection",
        default=False)

    tile_name: bpy.props.StringProperty(
        name="Tile Name"
    )

    # Tile type #
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
        items=create_tile_type_enums,
        name="Type",
        description="The type of tile e.g. Straight Wall, Curved Floor"
    )

    # Native Subdivisions #
    x_native_subdivisions: bpy.props.IntProperty(
        name="X",
        description="The number of times to subdivide the X axis on creation",
        default=15
    )

    y_native_subdivisions: bpy.props.IntProperty(
        name="Y",
        description="The number of times to subdivide the Y axis on creation",
        default=3
    )

    z_native_subdivisions: bpy.props.IntProperty(
        name="Z",
        description="The number of times to subdivide the Z axis on creation",
        default=15
    )

    opposite_native_subdivisions: bpy.props.IntProperty(
        name="Opposite Side",
        description="The number of times to subdivide the edge opposite the root angle on triangular tile creation",
        default=15
    )

    curve_native_subdivisions: bpy.props.IntProperty(
        name="Curved Side",
        description="The number of times to subdivide the curved side of a tile",
        default=15
    )

    leg_1_native_subdivisions: bpy.props.IntProperty(
        name="Leg 1",
        description="The number of times to subdivide the length of leg 1 of the tile",
        default=15
    )

    leg_2_native_subdivisions: bpy.props.IntProperty(
        name="Leg 2",
        description="The number of times to subdivide the length of leg 2 of the tile",
        default=15
    )

    width_native_subdivisions: bpy.props.IntProperty(
        name="Width",
        description="The number of times to subdivide each leg along its width",
        default=3
    )

    # Subsurf modifier subdivisions #
    subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        description="Subsurf modifier subdivision levels",
        default=3
    )

    # UV smart projection correction
    UV_island_margin: bpy.props.FloatProperty(
        name="UV Margin",
        default=0.012,
        min=0,
        step=0.001,
        description="Tweak this if you have gaps at edges of tiles when you Make3D"
    )

    # Dimensions #
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

    openlock_column_type: bpy.props.EnumProperty(
        items=openlock_column_types,
        name="Column type"
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


def register():
    # Property group containing radio buttons
    bpy.types.WindowManager.mt_radio_buttons = bpy.props.PointerProperty(
        type=MT_Radio_Buttons
    )

    # Property group that contains properties set in UI
    bpy.types.Scene.mt_scene_props = bpy.props.PointerProperty(
        type=MT_Scene_Properties
    )

    # Property group that contains properties of an object stored on the object
    bpy.types.Object.mt_object_props = bpy.props.PointerProperty(
        type=MT_Object_Properties
    )

    # Property group that contains properties relating to a tile stored on the tile collection
    bpy.types.Collection.mt_tile_props = bpy.props.PointerProperty(
        type=MT_Tile_Properties
    )


def unregister():
    del bpy.types.WindowManager.mt_radio_buttons
    del bpy.types.Object.mt_object_props
    del bpy.types.Collection.mt_tile_props
    del bpy.types.Scene.mt_scene_props
