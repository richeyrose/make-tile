import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    PointerProperty)

from ..enums.enums import (
    tile_blueprints,
    units,
    openlock_column_types,
    column_socket_style,
    collection_types)

from ..tile_creation.create_tile import (
    MT_Tile_Generator)

from ..lib.utils.utils import get_all_subclasses, get_annotations

# TODO Decide how many of these properties we actually need to be storing.
# TODO rename to mt_collection_props
'''

class MT_Tile_Properties(PropertyGroup):
    is_mt_collection: BoolProperty(
        name="Is MakeTile collection",
        default=False)

    tile_name: StringProperty(
        name="Tile Name"
    )

    collection_type: EnumProperty(
        items=collection_types,
        name="Collection Types",
        description="Easy way of distinguishing whether we are dealing with a tile, \
            an architectural element or a larger prefab such as a building or dungeon."
    )

    # Tile type #
    tile_blueprint: EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        description="Blueprint for entire tile - e.g. openLOCK or Plain")

    tile_material_1: EnumProperty(
        items=create_material_enums,
        name="Material"
    )

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        name="Core"
    )

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        name="Base"
    )

    tile_type: EnumProperty(
        items=create_tile_type_enums,
        name="Type",
        description="The type of tile e.g. Straight Wall, Curved Floor"
    )

    # Native Subdivisions
    subdivision_density: EnumProperty(
        items=[
            ("HIGH", "High", "", 1),
            ("MEDIUM", "Medium", "", 2),
            ("LOW", "Low", "", 3)],
        default="MEDIUM",
        name="Subdivision Density")

    # Subsurf modifier subdivisions #
    subdivisions: IntProperty(
        name="Subdivisions",
        description="Subsurf modifier subdivision levels",
        default=3
    )

    # UV smart projection correction
    UV_island_margin: FloatProperty(
        name="UV Margin",
        default=0.012,
        min=0,
        step=0.001,
        description="Tweak this if you have gaps at edges of tiles when you Make3D"
    )

    # stops texture projecting beyond bounds of vert group
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

    # Dimensions #
    tile_size: FloatVectorProperty(
        name="Tile Size"
    )

    base_size: FloatVectorProperty(
        name="Base size"
    )

    base_radius: FloatProperty(
        name="Base Radius"
    )

    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base.")],
        default="CENTER")

    # used for S_Walls
    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)

    wall_radius: FloatProperty(
        name="Wall Radius"
    )

    base_socket_side: EnumProperty(
        name="Socket Side",
        items=base_socket_side
    )

    degrees_of_arc: FloatProperty(
        name="Degrees of Arc"
    )

    angle: FloatProperty(
        name="Angle"
    )

    leg_1_len: FloatProperty(
        name="Leg 1 Length"
    )

    leg_2_len: FloatProperty(
        name="Leg 2 Length"
    )

    curve_type: EnumProperty(
        name="Curve Type",
        items=curve_types
    )

    column_type: EnumProperty(
        items=openlock_column_types,
        name="Column type"
    )

    column_socket_style: EnumProperty(
        name="Socket Style",
        items=column_socket_style,
        default="TEXTURED"
    )

    tile_units: EnumProperty(
        name="Tile Units",
        items=units
    )

    tile_resolution: IntProperty(
        name="Tile Resolution"
    )
'''

def create_tile_props():
    """Dynamically create new_mt_tile_props PropertyGroup based on properties in MT_Tile_Generator and subclasses."""
    subclasses = get_all_subclasses(MT_Tile_Generator)
    annotations = {}

    for subclass in subclasses:
        # make sure we also get annotations of parent classes such as mixins
        annotations.update(get_annotations(subclass))
        annotations.update(subclass.__annotations__)

    New_MT_Tile_Props = type(
        'New_MT_Tile_Props',
        (PropertyGroup,),
        {'__annotations__':
            annotations})
    bpy.utils.register_class(New_MT_Tile_Props)
    PointerTileProps = PointerProperty(type=New_MT_Tile_Props)
    setattr(bpy.types.Collection, "mt_tile_props", PointerTileProps)

def register():
    # Property group that contains properties relating to a tile stored on the tile collection
    '''
    bpy.types.Collection.mt_tile_props = PointerProperty(
        type=MT_Tile_Properties
    )
    '''
    create_tile_props()

def unregister():
    #del bpy.types.Collection.new_mt_tile_props
    del bpy.types.Collection.mt_tile_props
