import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty,
    PointerProperty)


from ..tile_creation.create_tile import (
    MT_Tile_Generator)

from ..lib.utils.utils import get_all_subclasses, get_annotations

from ..tile_creation.create_tile import create_tile_type_enums

def create_tile_props():
    """Dynamically create new_mt_tile_props PropertyGroup based on properties in MT_Tile_Generator and subclasses."""

    props = {
        "tile_type": EnumProperty(
            items=create_tile_type_enums,
            name="Tile Type",
            description="The type of tile e.g. Straight Wall, Curved Floor"
        )
    }
    subclasses = get_all_subclasses(MT_Tile_Generator)
    annotations = {}

    for subclass in subclasses:
        # make sure we also get annotations of parent classes such as mixins
        annotations.update(get_annotations(subclass))
        annotations.update(subclass.__annotations__)
        annotations.update(props)

    New_MT_Tile_Props = type(
        'New_MT_Tile_Props',
        (PropertyGroup,),
        {'__annotations__':
            annotations})
    bpy.utils.register_class(New_MT_Tile_Props)
    PointerTileProps = PointerProperty(type=New_MT_Tile_Props)
    setattr(bpy.types.Collection, "mt_tile_props", PointerTileProps)

def register():
    create_tile_props()

def unregister():
    #del bpy.types.Collection.new_mt_tile_props
    del bpy.types.Collection.mt_tile_props
