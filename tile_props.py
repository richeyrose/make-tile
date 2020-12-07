import bpy
from bpy.types import PropertyGroup
from . enums.enums import (
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

#TODO rename to mt_collection_props

class MT_Tile_Properties(PropertyGroup):
    is_mt_collection: bpy.props.BoolProperty(
        name="Is MakeTile collection",
        default=False)

    tile_name: bpy.props.StringProperty(
        name="Tile Name"
    )

    collection_type: bpy.props.EnumProperty(
        items=collection_types,
        name="Collection Types",
        description="Easy way of distinguishing whether we are dealing with a tile, an architectural element or a larger prefab such as a builing or dungeon."
    )

    # Tile type #
    tile_blueprint: bpy.props.EnumProperty(
        items=tile_blueprints,
        name="Blueprint",
        description="Blueprint for entire tile - e.g. openLOCK or Plain")

    main_part_blueprint: bpy.props.EnumProperty(
        items=create_main_part_blueprint_enums,
        name="Core"
    )

    base_blueprint: bpy.props.EnumProperty(
        items=create_base_blueprint_enums,
        name="Base"
    )

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

    # stops texture projecting beyond bounds of vert group
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

    column_type: bpy.props.EnumProperty(
        items=openlock_column_types,
        name="Column type"
    )

    column_socket_style: bpy.props.EnumProperty(
        name="Socket Style",
        items=column_socket_style,
        default="TEXTURED"
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
    # Property group that contains properties relating to a tile stored on the tile collection
    bpy.types.Collection.mt_tile_props = bpy.props.PointerProperty(
        type=MT_Tile_Properties
    )


def unregister():
    del bpy.types.Collection.mt_tile_props
