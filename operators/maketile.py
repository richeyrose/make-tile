"""Contains operator class to make tiles"""
import bpy
from mathutils import Vector
from .. tile_creation.create_tile import create_tile
from .. enums.enums import tile_main_systems, tile_types, units, base_systems, tile_materials, tile_blueprints
from .. utils.registration import get_prefs


class MT_OT_Make_Tile(bpy.types.Operator):
    """Operator class used to create tiles"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"

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
            base_system,
            tile_material
        )

        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        preferences = get_prefs()

        bpy.types.Scene.mt_tile_units = bpy.props.EnumProperty(
            items=units,
            name="Tile Units",
            default=preferences.default_units,
        )

        bpy.types.Scene.mt_tile_blueprint = bpy.props.EnumProperty(
            items=tile_blueprints,
            name="Tile Blueprint",
            default=preferences.default_tile_blueprint,
        )

        bpy.types.Scene.mt_tile_main_system = bpy.props.EnumProperty(
            items=tile_main_systems,
            name="Tile Main System",
            default=preferences.default_tile_main_system,
        )
        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Tile Type",
            default="STRAIGHT_WALL",
        )

        bpy.types.Scene.mt_base_system = bpy.props.EnumProperty(
            items=base_systems,
            name="Base Types",
            default=preferences.default_base_system,
        )

        bpy.types.Scene.mt_tile_material = bpy.props.EnumProperty(
            items=tile_materials,
            name="Tile Material",
            default="STONEWALL1",
        )

        # Tile and base Size. We use seperate floats so that we can only show
        # customisable ones where appropriate. These are wrapped up
        # in a vector and passed on as tile_size and base_size

        # Tile size
        bpy.types.Scene.mt_tile_x = bpy.props.FloatProperty(
            name="Tile X",
            default=2.0,
            step=0.5,
            precision=3,
        )

        bpy.types.Scene.mt_tile_y = bpy.props.FloatProperty(
            name="Tile Y",
            default=2,
            step=0.5,
            precision=3,
        )

        bpy.types.Scene.mt_tile_z = bpy.props.FloatProperty(
            name="Tile Z",
            default=2.0,
            step=0.1,
            precision=3,
        )

        # Base size
        bpy.types.Scene.mt_base_x = bpy.props.FloatProperty(
            name="Base X",
            default=2.0,
            step=0.5,
            precision=3,
        )

        bpy.types.Scene.mt_base_y = bpy.props.FloatProperty(
            name="Base Y",
            default=0.5,
            step=0.5,
            precision=3,
        )
        bpy.types.Scene.mt_base_z = bpy.props.FloatProperty(
            name="Base Z",
            default=0.3,
            step=0.1,
            precision=3,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_base_x
        del bpy.types.Scene.mt_base_y
        del bpy.types.Scene.mt_base_z
        del bpy.types.Scene.mt_tile_x
        del bpy.types.Scene.mt_tile_y
        del bpy.types.Scene.mt_tile_z
        del bpy.types.Scene.mt_base_system
        del bpy.types.Scene.mt_tile_material
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_blueprint
        del bpy.types.Scene.mt_tile_main_system
        del bpy.types.Scene.mt_tile_units
