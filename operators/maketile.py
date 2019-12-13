"""Contains operator class to make tiles"""
import os
import bpy
import bpy.utils.previews
from mathutils import Vector
from .. utils.registration import get_path, get_prefs
from .. tile_creation.create_tile import create_tile

from .. enums.enums import (
    tile_main_systems,
    tile_types,
    units,
    base_systems,
    tile_blueprints,
    base_socket_side)

from .. materials.materials import (
    load_materials,
    get_blend_filenames,
    assign_displacement_materials,
    assign_preview_materials,
    update_displacement_material,
    update_preview_material)


class MT_OT_Make_Tile(bpy.types.Operator):
    """Operator class used to create tiles"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):

        tile_blueprint = context.scene.mt_tile_blueprint
        tile_main_system = context.scene.mt_tile_main_system
        tile_type = context.scene.mt_tile_type
        tile_size = Vector((context.scene.mt_tile_x, context.scene.mt_tile_y, context.scene.mt_tile_z))
        base_size = Vector((context.scene.mt_base_x, context.scene.mt_base_y, context.scene.mt_base_z))
        base_inner_radius = bpy.context.scene.mt_base_inner_radius
        wall_inner_radius = bpy.context.scene.mt_wall_inner_radius
        degrees_of_arc = bpy.context.scene.mt_degrees_of_arc
        segments = bpy.context.scene.mt_segments
        socket_side = bpy.context.scene.mt_base_socket_side
        base_system = context.scene.mt_base_system
        tile_material = context.scene.mt_tile_material

        if tile_blueprint == 'OPENLOCK':
            tile_main_system = 'OPENLOCK'
            base_system = 'OPENLOCK'

        if tile_blueprint == 'PLAIN':
            tile_main_system = 'PLAIN'
            base_system = 'PLAIN'

        create_tile(
            tile_blueprint,
            tile_main_system,
            tile_type,
            tile_size,
            base_size,
            base_inner_radius,
            wall_inner_radius,
            degrees_of_arc,
            segments,
            base_system,
            tile_material,
            socket_side
        )

        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        preferences = get_prefs()
        material_enum_collection = bpy.utils.previews.new()
        material_enum_collection.directory = ''
        material_enum_collection.enums = ()
        enum_collections["materials"] = material_enum_collection

        bpy.types.Scene.mt_tile_units = bpy.props.EnumProperty(
            items=units,
            name="Units",
            default=preferences.default_units,
        )

        bpy.types.Scene.mt_tile_blueprint = bpy.props.EnumProperty(
            items=tile_blueprints,
            name="Blueprint",
            default=preferences.default_tile_blueprint,
        )

        bpy.types.Scene.mt_tile_main_system = bpy.props.EnumProperty(
            items=tile_main_systems,
            name="Main System",
            default=preferences.default_tile_main_system,
        )
        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Type",
            default="STRAIGHT_WALL",
        )

        bpy.types.Scene.mt_base_system = bpy.props.EnumProperty(
            items=base_systems,
            name="Base Type",
            default=preferences.default_base_system,
        )

        bpy.types.Scene.mt_tile_material = bpy.props.EnumProperty(
            items=load_material_enums,
            name="Material",
            update=update_material,
        )

        bpy.types.Scene.mt_tile_resolution = bpy.props.IntProperty(
            name="Resolution",
            description="Bake resolution of displacement maps. Higher = better quality but slower",
            default=1024,
            min=1024,
            max=8192,
            step=1024,
        )

        bpy.types.Scene.mt_subdivisions = bpy.props.IntProperty(
            name="Subdivisions",
            description="How many times to subdivide the displacement mesh. Higher = better but slower. \
            Going above 8 is really not recommended and may cause Blender to freeze up for a loooooong time!",
            default=7,
            soft_max=8,
        )

        # Tile and base size. We use seperate floats so that we can only show
        # customisable ones where appropriate. These are wrapped up
        # in a vector and passed on as tile_size and base_size

        # Tile size
        bpy.types.Scene.mt_tile_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_y = bpy.props.FloatProperty(
            name="Y",
            default=2,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_z = bpy.props.FloatProperty(
            name="Z",
            default=2.0,
            step=0.1,
            precision=3,
            min=0
        )

        # Base size
        bpy.types.Scene.mt_base_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_base_y = bpy.props.FloatProperty(
            name="Y",
            default=0.5,
            step=0.5,
            precision=3,
            min=0
        )
        bpy.types.Scene.mt_base_z = bpy.props.FloatProperty(
            name="Z",
            default=0.3,
            step=0.1,
            precision=3,
            min=0
        )

        # Openlock curved wall specific
        bpy.types.Scene.mt_base_socket_side = bpy.props.EnumProperty(
            items=base_socket_side,
            name="Socket Side",
            default="INNER",
        )

        # Used for curved wall tiles
        bpy.types.Scene.mt_base_inner_radius = bpy.props.FloatProperty(
            name="Base inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0,
        )

        bpy.types.Scene.mt_wall_inner_radius = bpy.props.FloatProperty(
            name="Wall inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
        bpy.types.Scene.mt_degrees_of_arc = bpy.props.FloatProperty(
            name="Degrees of arc",
            default=90,
            step=45,
            precision=1,
            max=359.999,
            min=1
        )

        bpy.types.Scene.mt_segments = bpy.props.IntProperty(
            name="Number of segments",
            default=32,
        )

        bpy.types.Scene.mt_tile_name = bpy.props.StringProperty(
            name="Tile Name",
            default="Tile"
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_tile_name
        del bpy.types.Scene.mt_segments
        del bpy.types.Scene.mt_base_inner_radius
        del bpy.types.Scene.mt_wall_inner_radius
        del bpy.types.Scene.mt_degrees_of_arc
        del bpy.types.Scene.mt_base_socket_side
        del bpy.types.Scene.mt_base_x
        del bpy.types.Scene.mt_base_y
        del bpy.types.Scene.mt_base_z
        del bpy.types.Scene.mt_tile_x
        del bpy.types.Scene.mt_tile_y
        del bpy.types.Scene.mt_tile_z
        del bpy.types.Scene.mt_base_system
        del bpy.types.Scene.mt_tile_resolution
        del bpy.types.Scene.mt_tile_material
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_blueprint
        del bpy.types.Scene.mt_tile_main_system
        del bpy.types.Scene.mt_tile_units

        for pcoll in enum_collections.values():
            bpy.utils.previews.remove(pcoll)
        enum_collections.clear()


def load_material_enums(self, context):
    enum_items = []
    preferences = get_prefs()
    if context is None:
        return enum_items

    materials_path = os.path.join(preferences.assets_path, "materials")
    blend_filenames = get_blend_filenames(materials_path)
    enum_collection = enum_collections['materials']
    if materials_path == enum_collection.directory:
        return enum_collection.enums

    load_materials(materials_path, blend_filenames)
    materials = bpy.data.materials
    for material in materials:
        # prevent make-tile adding the default material to the list
        if material.name != 'Material':
            enum = (material.name, material.name, "")
            enum_items.append(enum)

    enum_collection.enums = enum_items
    enum_collection.directory = materials_path
    return enum_collection.enums


def update_material(self, context):
    preview_obj = bpy.context.object

    if 'geometry_type' in preview_obj:
        if preview_obj['geometry_type'] == 'PREVIEW':
            disp_obj = preview_obj['displacement_obj']
            update_displacement_material(disp_obj, bpy.context.scene.mt_tile_material)
            update_preview_material(preview_obj, bpy.context.scene.mt_tile_material)


enum_collections = {}
