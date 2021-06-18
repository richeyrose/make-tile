import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty)
from ..enums.enums import (
    units,
    material_mapping)
from ..tile_creation.create_tile import MT_Tile_Generator
from ..lib.utils.utils import get_all_subclasses, get_annotations
from ..tile_creation.create_tile import create_tile_type_enums
from ..app_handlers import load_tile_defaults

"""
def update_UV_island_margin(self, context):
    '''Reruns UV smart project for preview and displacement object'''

    if len(bpy.context.selected_editable_objects) > 0:
        obj = bpy.context.object
        if obj.type == 'MESH':
            obj_props = obj.mt_object_props
            # if obj_props.geometry_type in ('DISPLACEMENT', 'PREVIEW'):
            if obj_props.is_displacement:

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

                bpy.ops.object.editmode_toggle(ctx)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.editmode_toggle(ctx)
"""

def update_disp_strength(self, context):
    """Update the displacement strength of the maketile displacement modifier on active object.

    Args:
        context (bpy.context): context
    """
    obj = bpy.context.active_object
    if context.active_object.select_get():
        obj_props = obj.mt_object_props
        obj_props.displacement_strength = context.scene.mt_scene_props.displacement_strength
        try:
            obj.modifiers[obj_props.disp_mod_name].strength = context.scene.mt_scene_props.displacement_strength
        except KeyError:
            pass


def update_disp_subdivisions(self, context):
    """Update the number of subdivisions used by the displacement material modifier."""

    selected = [ob for ob in context.selected_editable_objects if ob.mt_object_props.is_displacement]
    for obj in selected:
        obj_props = obj.mt_object_props
        try:
            obj.modifiers[obj_props.subsurf_mod_name].levels = context.scene.mt_scene_props.subdivisions
        except KeyError:
            pass


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


'''
class MT_Scene_Properties(PropertyGroup):
    """Contains MakeTile scene properties.
    Used to store properties that can be set by user for tile generation etc.

    Args:
        PropertyGroup (bpy.types.PropertyGroup): Group of ID properties
    """

    mt_is_just_activated: BoolProperty(
        description="Has the add-on just been activated. Used to populate materials list first time round",
        default=False
    )

    mt_last_selected: PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object
    )

    tile_type: EnumProperty(
        items=create_tile_type_enums,
        name="Tile Type",
        update=update_scene_defaults
    )

    tile_name: StringProperty(
        name="Tile Name",
        default="Tile"
    )

    tile_units: EnumProperty(
        items=units,
        name="Units",
        default='INCHES'
    )

    tile_blueprint: EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        default="CUSTOM"
    )

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        update=update_main_part_defaults,
        name="Core"
    )

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_base_defaults,
        name="Base"
    )

    UV_island_margin: FloatProperty(
        name="UV Margin",
        default=0.01,
        precision=4,
        min=0,
        step=0.1,
        description="Tweak this if you have gaps in material at edges of tiles when you Make3D",
        update=update_UV_island_margin
    )

    # Native Subdivisions #
    subdivision_density: EnumProperty(
        items=[
            ("HIGH", "High", "", 1),
            ("MEDIUM", "Medium", "", 2),
            ("LOW", "Low", "", 3)],
        default="MEDIUM",
        name="Subdivision Density")

    material_mapping_method: EnumProperty(
        items=material_mapping,
        description="How to map the active material onto an object",
        name="Material Mapping Method",
        update=update_material_mapping,
        default='OBJECT'
    )

    displacement_strength: FloatProperty(
        name="Displacement Strength",
        description="Overall Displacement Strength",
        default=0.1,
        step=1,
        precision=3,
        update=update_disp_strength
    )

    tile_material_1: EnumProperty(
        items=create_material_enums,
        name="Material"
    )

    tile_resolution: IntProperty(
        name="Resolution",
        description="Bake resolution of displacement maps. Higher = better quality but slower. Also images are 32 bit so 4K and 8K images can be gigabytes in size",
        default=1024,
        min=1024,
        max=8192,
        step=1024,
    )



    texture_margin: FloatProperty(
        name="Texture Margin",
        description="Margin around displacement texture. Used for correcting distortion",
        default=0.001,
        min=0.0001,
        soft_max=0.1,
        step=0.0001
    )


    # used for where it makes sense to set displacement thickness directly rather than
    # as an offset between base and core. e.g. connecting columns
    displacement_thickness: FloatProperty(
        name="Displacement Thickness",
        description="Thickness of displacement texture.",
        default=0.05
    )

    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base.")],
        default="CENTER")

    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)

    # Tile and base size. We use seperate floats so that we can only show
    # customisable ones where appropriate. These are wrapped up
    # in a vector and passed on as tile_size and base_size

    # Scale base proportionate to tile
    x_proportionate_scale: BoolProperty(
        name="X",
        default=True
    )

    y_proportionate_scale: BoolProperty(
        name="Y",
        default=False
    )

    z_proportionate_scale: BoolProperty(
        name="Z",
        default=False
    )

    # Tile size
    tile_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=1,
        update=update_base_x,
        min=0
    )

    tile_y: FloatProperty(
        name="Y",
        default=2,
        step=50,
        precision=1,
        update=update_base_y,
        min=0
    )

    tile_z: FloatProperty(
        name="Z",
        default=2.0,
        step=50,
        precision=1,
        update=update_base_z,
        min=0
    )

    # Base size
    base_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=1,
        min=0
    )

    base_y: FloatProperty(
        name="Y",
        default=0.5,
        step=50,
        precision=1,
        min=0
    )

    base_z: FloatProperty(
        name="Z",
        default=0.3,
        step=50,
        precision=2,
        min=0
    )

    # Corner wall and triangular base specific
    angle: FloatProperty(
        name="Base Angle",
        default=90,
        step=5,
        precision=1
    )

    leg_1_len: FloatProperty(
        name="Leg 1 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    leg_2_len: FloatProperty(
        name="Leg 2 Length",
        description="Length of leg",
        default=2,
        step=50,
        precision=1
    )

    # Openlock curved wall specific
    base_socket_side: EnumProperty(
        items=base_socket_side,
        name="Socket Side",
        default="INNER",
    )

    # Used for curved wall tiles
    base_radius: FloatProperty(
        name="Base inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0,
    )

    wall_radius: FloatProperty(
        name="Wall inner radius",
        default=2.0,
        step=50,
        precision=1,
        min=0
    )

    # used for curved floors
    curve_type: EnumProperty(
        items=curve_types,
        name="Curve type",
        default="POS",
        description="Whether the tile has a positive or negative curvature"
    )

    curve_texture: BoolProperty(
        name="Curve Texture",
        description="Setting this to true will make the texture follow the curve of the tile. Useful for decorative elements, borders etc.",
        default=False,
        update=update_curve_texture
    )

    # Connecting column specific
    column_type: EnumProperty(
        items=openlock_column_types,
        name="Column type",
        default="O"
    )

    column_socket_style: EnumProperty(
        name="Socket Style",
        items=column_socket_style,
        default="TEXTURED",
        description="Whether to have texture on the sides with sockets."
    )

    # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
    degrees_of_arc: FloatProperty(
        name="Degrees of arc",
        default=90,
        step=45,
        precision=1,
        max=359.999,
        min=0
    )

    # used for rescaling objects
    base_unit: EnumProperty(
        name="Base Unit",
        items=units
    )

    target_unit: EnumProperty(
        name="Target Unit",
        items=units
    )

    # voxel properties
    voxel_size: FloatProperty(
        name="Voxel Size",
        description="Quality of the voxelisation. Smaller = Better",
        soft_min=0.005,
        default=0.0051,
        precision=3,
    )

    voxel_adaptivity: FloatProperty(
        name="Adaptivity",
        description="Amount by which to simplify mesh",
        default=0.25,
        precision=3,
    )

    voxel_merge: BoolProperty(
        name="Merge",
        description="Merge objects on voxelisation? Creates a single mesh.",
        default=True
    )

    # decimator properties
    decimation_ratio: FloatProperty(
        name="Decimation Ratio",
        description="Amount to decimate by. Smaller = more simplification",
        min=0.0,
        max=1,
        precision=3,
        step=0.01,
        default=0.25
    )

    decimation_merge: BoolProperty(
        name="Merge",
        description="Merge selected before decimation",
        default=True
    )

    planar_decimation: BoolProperty(
        name="Planar Decimation",
        description="Further simplify the planar (flat) parts of the mesh",
        default=False
    )

    planar_decimation_angle: FloatProperty(
        name="Decimation Angle",
        description="Angle below which to simplify",
        default=5,
        max=90,
        min=0,
        step=5
    )

    # Add to tile properties
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers to object before adding it?",
        default=True)

    boolean_type: EnumProperty(
        name="Boolean Type",
        items=[
            ("UNION", "Union", ""),
            ("DIFFERENCE", "Difference", "")
        ],
        default="UNION",
        description="Whether to add (Union) or subtract (Difference) object from tile.")

    # Exporter properties
    num_variants: IntProperty(
        name="Variants",
        description="Number of variants of tile to export",
        default=1
    )

    randomise_on_export: BoolProperty(
        name="Randomise",
        description="Create random variant on export?",
        default=True
    )

    voxelise_on_export: BoolProperty(
        name="Voxelise",
        default=True
    )

    decimate_on_export: BoolProperty(
        name="Decimate",
        default=False
    )

    export_units: EnumProperty(
        name="Units",
        items=units,
        description="Export units",
        default='INCHES'
    )

    fix_non_manifold: BoolProperty(
        name="Fix non-manifold",
        description="Attempt to fix geometry errors",
        default=False
    )

    export_subdivs: IntProperty(
        name="Export Subdivisions",
        description="Subdivision levels of exported tile",
        default=3
    )

    wall_blueprint: EnumProperty(
        name="Wall Blueprint",
        items=[
            ("OPENLOCK", "OpenLOCK",""),
            ("PLAIN", "Plain", ""),
            ("NONE", "None", "")],
        #update=update_wall_blueprint,
        default="OPENLOCK"
    )
'''

def reset_part_defaults(self, context):
    tile_type = self.tile_type
    base_blueprint = self.base_blueprint
    main_part_blueprint = self.main_part_blueprint
    tile_defaults = load_tile_defaults(context)
    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            base_defaults = defaults['base_defaults']
            for key, value in base_defaults.items():
                if key == base_blueprint:
                    for k, v in value.items():
                        setattr(self, k, v)
                    break
            main_part_defaults = defaults['tile_defaults']
            for key, value in main_part_defaults.items():
                if key == main_part_blueprint:
                    for k, v in value.items():
                        setattr(self, k, v)
                    break

def update_scene_defaults(self, context):
    tile_type = self.tile_type
    tile_defaults = load_tile_defaults(context)
    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            for key, value in defaults.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            break
    reset_part_defaults(self, context)

def create_scene_props():
    """Dynamically create MT_Scene_Props property group.
    """

    # Manually created properties for exporter etc.
    props = {
        "displacement_strength": FloatProperty(
            name="Displacement Strength",
            description="Overall Displacement Strength",
            default=0.1,
            step=1,
            precision=3,
            update=update_disp_strength),
        "mt_last_selected": PointerProperty(
            name="Last Selected Object",
            type=bpy.types.Object),
        "material_mapping_method": EnumProperty(
            items=material_mapping,
            description="How to map the active material onto an object",
            name="Material Mapping Method",
            update=update_material_mapping,
            default='OBJECT'),
        "base_unit": EnumProperty(
            name="Base Unit",
            items=units),
        "target_unit": EnumProperty(
            name="Target Unit",
            items=units),
        "tile_resolution": IntProperty(
            name="Resolution",
            description="Bake resolution of displacement maps. Higher = better quality but slower. Also images are 32 bit so 4K and 8K images can be gigabytes in size",
            default=1024,
            min=1024,
            max=8192,
            step=1024),
        "voxel_size": FloatProperty(
            name="Voxel Size",
            description="Quality of the voxelisation. Smaller = Better",
            soft_min=0.005,
            default=0.0051,
            precision=3),
        "voxel_adaptivity": FloatProperty(
            name="Adaptivity",
            description="Amount by which to simplify mesh",
            default=0.25,
            precision=3),
        "voxel_merge": BoolProperty(
            name="Merge",
            description="Merge objects on voxelisation? Creates a single mesh.",
            default=True),
        "fix_non_manifold": BoolProperty(
            name="Fix non-manifold",
            description="Attempt to fix geometry errors",
            default=False),
        "decimation_ratio": FloatProperty(
            name="Decimation Ratio",
            description="Amount to decimate by. Smaller = more simplification",
            min=0.0,
            max=1,
            precision=3,
            step=0.01,
            default=0.25),
        "decimation_merge": BoolProperty(
            name="Merge",
            description="Merge selected before decimation",
            default=True),
        "planar_decimation": BoolProperty(
            name="Planar Decimation",
            description="Further simplify the planar (flat) parts of the mesh",
            default=False),
        "planar_decimation_angle": FloatProperty(
            name="Decimation Angle",
            description="Angle below which to simplify",
            default=5,
            max=90,
            min=0,
            step=5),
        "num_variants": IntProperty(
            name="Variants",
            description="Number of variants of tile to export",
            default=1),
        "randomise_on_export": BoolProperty(
            name="Randomise",
            description="Create random variant on export?",
            default=True),
        "voxelise_on_export": BoolProperty(
            name="Voxelise",
            default=True),
        "decimate_on_export": BoolProperty(
            name="Decimate",
            default=False),
        "export_units": EnumProperty(
            name="Units",
            items=units,
            description="Export units",
            default='INCHES'),
        "subdivisions": IntProperty(
            name="Subdivisions",
            description="How many times to subdivide the displacement mesh with a subsurf modifier. Higher = better but slower.",
            default=3,
            soft_max=8,
            update=update_disp_subdivisions),
        # rather than creating this in the the MT_Tile_Generator class and copying it we set it seperately here
        # and in the tile_props to allow us to have different update functions
        "tile_type": EnumProperty(
            items=create_tile_type_enums,
            name="Tile Type",
            update=update_scene_defaults,
            description="The type of tile e.g. Straight Wall, Curved Floor"
        ),
        "is_scene_props": BoolProperty(
            default=True)
    }

    # dynamically created properties constructed from all annotations in subclasses of MT_Tile_Generator
    subclasses = get_all_subclasses(MT_Tile_Generator)
    annotations = {}


    for subclass in subclasses:
        # make sure we also get annotations of parent classes such as mixins
        annotations.update(get_annotations(subclass))
        annotations.update(subclass.__annotations__)
        annotations.update(props)

    # exclusion list
    exclude = ["invoked", "executed"]
    for item in exclude:
        del annotations[item]

    MT_Scene_Props = type(
        'New_MT_Scene_Props',
        (PropertyGroup,),
        {'__annotations__': annotations})
    bpy.utils.register_class(MT_Scene_Props)
    PointerSceneProps = PointerProperty(type=MT_Scene_Props)
    setattr(bpy.types.Scene, "mt_scene_props", PointerSceneProps)

def register():
    create_scene_props()

def unregister():
    del bpy.types.Scene.mt_scene_props
