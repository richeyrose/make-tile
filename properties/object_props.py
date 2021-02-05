import bpy
from bpy.types import PropertyGroup
from ..enums.enums import geometry_types, boolean_types
# A cutter item used by cutters_collection


class MT_Cutter_Item(PropertyGroup):
    def update_use_cutter(self, context):
        if self.parent is not "":
            parent_obj = bpy.data.objects[self.parent]
            bool_mod = parent_obj.modifiers[self.name + '.bool']
            bool_mod.show_viewport = self.value

    name: bpy.props.StringProperty(
        name="Cutter Name")
    value: bpy.props.BoolProperty(
        name="",
        default=True,
        update=update_use_cutter)
    parent: bpy.props.StringProperty(
        name="")


class MT_Preview_Materials(PropertyGroup):
    """Used to store a list of preview materials during baking.

    When we hit the Make3D button maketile assigns the secondary material to the entire
    mesh so we only see actual displacement. We store what materials have been assigned
    to what vertex groups here so we can reassign them to the object later

    Args:
        PropertyGroup (bpy.types.PropertyGroup): Parent class
    """

    vertex_group: bpy.props.StringProperty(
        name="vertex group"
    )

    material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="material"
    )


class MT_Object_Properties(PropertyGroup):
    is_mt_object: bpy.props.BoolProperty(
        name="Is MakeTile Object",
        default=False
    )

    is_converted: bpy.props.BoolProperty(
        name="Is Converted",
        default=False
    )

    is_displacement: bpy.props.BoolProperty(
        name="Is displacement",
        default=False,
        description="Whether this object is a displacement object that can be made3d"
    )

    is_displaced: bpy.props.BoolProperty(
        name="Is Displaced",
        default=False,
        description="Whether this displacement object is currently displaced."
    )

    boolean_type: bpy.props.EnumProperty(
        name="Boolean Type",
        items=boolean_types,
        description="How this object should act when added to a collection."
    )

    boolean_order: bpy.props.IntProperty(
        name="Boolean Order",
        default=0,
        description="Order from first to last object should be used as a boolean if it is part of a collection that is added to a tile."
    )

    affects_base: bpy.props.BoolProperty(
        name="Affects Base",
        default=False,
        description="Used for objects that are added to tiles as part of architectural element collection. Useful for e.g. making pin holes for hinges for doors"
    )

    tile_name: bpy.props.StringProperty(
        name="Tile Name"
    )

    geometry_type: bpy.props.EnumProperty(
        name="Geometry Type",
        items=geometry_types
    )

    cutters_collection: bpy.props.CollectionProperty(
        name="Cutters Collection",
        type=MT_Cutter_Item,
        description="Collection of booleans that can be turned on or off by MakeTile."
    )

    disp_mod_name: bpy.props.StringProperty(
        name="Displacement Modifier Name",
        default='MT Displacement'
    )

    displacement_strength: bpy.props.FloatProperty(
        name="Displacement Strength",
        default=0.1,
        step=0.001
    )

    subsurf_mod_name: bpy.props.StringProperty(
        name="Subsurf Modifier Name",
        default="MT Subsurf"
    )

    disp_texture: bpy.props.PointerProperty(
        name="Displacement Texture",
        type=bpy.types.ImageTexture
    )

    penstate: bpy.props.BoolProperty(
        name="Pen State",
        description="Used by bmturtle. If penstate is true turtle draws on move",
        default=False
    )

    preview_materials: bpy.props.CollectionProperty(
        name="Preview materials",
        type=MT_Preview_Materials
    )


def register():
    # Property group that contains properties of an object stored on the object
    bpy.types.Object.mt_object_props = bpy.props.PointerProperty(
        type=MT_Object_Properties
    )


def unregister():
    del bpy.types.Object.mt_object_props
