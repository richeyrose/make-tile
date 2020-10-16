import bpy
from bpy.types import PropertyGroup
from .enums.enums import (
    tile_blueprints,
    curve_types,
    base_socket_side,
    units,
    material_mapping,
    openlock_column_types,
    column_socket_style)
from .properties import (
    create_main_part_blueprint_enums,
    create_tile_type_enums,
    create_base_blueprint_enums)


def load_material_enums(self, context):
    """Create a list of enum items of materials compatible with the MakeTile material system.

    Args:
        context (bpy.context): context

    Returns:
        list[EnumPropertyItem]: enum items
    """
    enum_items = []
    if context is None:
        return enum_items

    materials = bpy.data.materials
    for material in materials:
        if 'mt_material' in material.keys():
            if material['mt_material']:
                enum = (material.name, material.name, "")
                enum_items.append(enum)
    return enum_items


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


def update_UV_island_margin(self, context):
    '''Reruns UV smart project for preview and displacement object'''

    if len(bpy.context.selected_editable_objects) > 0:
        obj = bpy.context.object
        if obj.type == 'MESH':
            obj_props = obj.mt_object_props
            if obj_props.geometry_type in ('DISPLACEMENT', 'PREVIEW'):

                tile = bpy.data.collections[obj_props.tile_name]
                tile_props = tile.mt_tile_props

                scene_props = context.scene.mt_scene_props
                UV_island_margin = scene_props.UV_island_margin
                tile_props.UV_island_margin = UV_island_margin

                ctx = {
                    'object': obj,
                    'active_object': obj,
                    'selected_objects': [obj],
                    'selected_editable_objects': [obj]}

                bpy.ops.uv.smart_project(ctx, island_margin=UV_island_margin)


def update_disp_strength(self, context):
    """Update the displacement strength of the maketile displacement modifier on active object.

    Args:
        context (bpy.context): context
    """
    obj = bpy.context.object
    obj_props = obj.mt_object_props
    tile = bpy.data.collections[obj_props.tile_name]
    tile.mt_tile_props.displacement_strength = context.scene.mt_scene_props.displacement_strength
    if obj_props.geometry_type == 'DISPLACEMENT':
        if obj_props.disp_mod_name in obj.modifiers:
            mod = obj.modifiers[obj_props.disp_mod_name]
            mod.strength = context.scene.mt_scene_props.displacement_strength


def update_disp_subdivisions(self, context):
    '''Updates the number of subdivisions used by the displacement material modifier'''
    obj = bpy.context.object
    obj_props = obj.mt_object_props
    if obj_props.geometry_type == 'DISPLACEMENT':
        subsurf_mod = obj_props.subsurf_mod_name
        if subsurf_mod in obj.modifiers:
            modifier = obj.modifiers[subsurf_mod]
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
        name="Core"
    )

    base_blueprint: bpy.props.EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_defaults,
        name="Base"
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
        step=1,
        precision=3,
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

    texture_margin: bpy.props.FloatProperty(
        name="Texture Margin",
        description="Margin around displacement texture. Used for correcting distortion",
        default=0.001,
        min=0.0001,
        soft_max=0.1,
        step=0.0001
    )

    # used for where it makes sense to set displacement thickness directly rather than
    # as an offset between base and core. e.g. connecting columns
    displacement_thickness: bpy.props.FloatProperty(
        name="Displacement Thickness",
        description="Thickness of displacement texture.",
        default=0.05
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

    # Connecting column specific
    column_type: bpy.props.EnumProperty(
        items=openlock_column_types,
        name="Column type",
        default="O"
    )

    column_socket_style: bpy.props.EnumProperty(
        name="Socket Style",
        items=column_socket_style,
        default="TEXTURED",
        description="Whether to have texture on the sides with sockets."
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

    # voxel properties
    voxel_size: bpy.props.FloatProperty(
        name="Voxel Size",
        description="Quality of the voxelisation. Smaller = Better",
        soft_min=0.005,
        default=0.0051,
        precision=3,
    )

    voxel_adaptivity: bpy.props.FloatProperty(
        name="Adaptivity",
        description="Amount by which to simplify mesh",
        default=0.25,
        precision=3,
    )

    voxel_merge: bpy.props.BoolProperty(
        name="Merge",
        description="Merge objects on voxelisation? Creates a single mesh.",
        default=True
    )

    # decimator properties
    decimation_ratio: bpy.props.FloatProperty(
        name="Decimation Ratio",
        description="Amount to decimate by. Smaller = more simplification",
        min=0.0,
        max=1,
        precision=3,
        step=0.01,
        default=0.25
    )

    decimation_merge: bpy.props.BoolProperty(
        name="Merge",
        description="Merge selected before decimation",
        default=True
    )

    planar_decimation: bpy.props.BoolProperty(
        name="Planar Decimation",
        description="Further simplify the planar (flat) parts of the mesh",
        default=False
    )

    planar_decimation_angle: bpy.props.FloatProperty(
        name="Decimation Angle",
        description="Angle below which to simplify",
        default=5,
        max=90,
        min=0,
        step=5
    )

    # exporter properties
    num_variants: bpy.props.IntProperty(
        name="Variants",
        description="Number of variants of tile to export",
        default=1
    )

    randomise_on_export: bpy.props.BoolProperty(
        name="Randomise",
        description="Create random variant on export?",
        default=True
    )

    voxelise_on_export: bpy.props.BoolProperty(
        name="Voxelise",
        default=True
    )

    decimate_on_export: bpy.props.BoolProperty(
        name="Decimate",
        default=False
    )

    export_units: bpy.props.EnumProperty(
        name="Units",
        items=units,
        description="Export units",
        default='INCHES'
    )

    fix_non_manifold: bpy.props.BoolProperty(
        name="Fix non-manifold",
        description="Attempt to fix geometry errors",
        default=True
    )


def register():
    # Property group that contains properties set in UI
    bpy.types.Scene.mt_scene_props = bpy.props.PointerProperty(
        type=MT_Scene_Properties
    )


def unregister():
    del bpy.types.Scene.mt_scene_props
