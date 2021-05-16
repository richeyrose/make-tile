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
    curve_types,
    base_socket_side,
    units,
    openlock_column_types,
    column_socket_style,
    collection_types)

from .properties import (
    create_main_part_blueprint_enums,
    create_tile_type_enums,
    create_base_blueprint_enums)
# TODO Decide how many of these properties we actually need to be storing.
# TODO rename to mt_collection_props


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

    x_native_subdivisions: IntProperty(
        name="X",
        description="The number of times to subdivide the X axis on creation",
        default=15
    )

    y_native_subdivisions: IntProperty(
        name="Y",
        description="The number of times to subdivide the Y axis on creation",
        default=3
    )

    z_native_subdivisions: IntProperty(
        name="Z",
        description="The number of times to subdivide the Z axis on creation",
        default=15
    )

    opposite_native_subdivisions: IntProperty(
        name="Opposite Side",
        description="The number of times to subdivide the edge opposite the root angle on triangular tile creation",
        default=15
    )

    curve_native_subdivisions: IntProperty(
        name="Curved Side",
        description="The number of times to subdivide the curved side of a tile",
        default=15
    )

    leg_1_native_subdivisions: IntProperty(
        name="Leg 1",
        description="The number of times to subdivide the length of leg 1 of the tile",
        default=15
    )

    leg_2_native_subdivisions: IntProperty(
        name="Leg 2",
        description="The number of times to subdivide the length of leg 2 of the tile",
        default=15
    )

    width_native_subdivisions: IntProperty(
        name="Width",
        description="The number of times to subdivide each leg along its width",
        default=3
    )

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


def register():
    # Property group that contains properties relating to a tile stored on the tile collection
    bpy.types.Collection.mt_tile_props = PointerProperty(
        type=MT_Tile_Properties
    )


def unregister():
    del bpy.types.Collection.mt_tile_props
