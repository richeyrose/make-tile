"""Contains operator class to make tiles"""
import bpy
from mathutils import Vector
from .. tile_creation.create_tile import create_tile
from .. enums.enums import tile_systems, tile_types, units, base_types
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

        scn = bpy.context.scene

        tile_system = scn.mt_tile_system
        tile_type = scn.mt_tile_type
        tile_size = Vector((scn.mt_tile_x, scn.mt_tile_y, scn.mt_tile_z))
        bhas_base = context.scene.mt_bhas_base
        base_size = Vector((scn.mt_base_x, scn.mt_base_y, scn.mt_base_z))
        tile_units = context.scene.mt_tile_units
        base_system = context.scene.mt_base_system

        create_tile(
            tile_units,
            tile_system,
            tile_type,
            bhas_base,
            tile_size,
            base_size,
            base_system
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

        bpy.types.Scene.mt_tile_system = bpy.props.EnumProperty(
            items=tile_systems,
            name="Tile System",
            default=preferences.default_tile_system,
        )
        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Tile Type",
            default="STRAIGHT_WALL",
        )

        bpy.types.Scene.mt_base_system = bpy.props.EnumProperty(
            items=base_types,
            name="Base Types",
            default=preferences.default_base_system,
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
            default=0.5,
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

        bpy.types.Scene.mt_bhas_base = bpy.props.BoolProperty(
            name="Seperate Base",
            description="Does this tile have a seperate base?",
            default=preferences.default_bhas_base,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_bhas_base
        del bpy.types.Scene.mt_base_x
        del bpy.types.Scene.mt_base_y
        del bpy.types.Scene.mt_base_z
        del bpy.types.Scene.mt_tile_x
        del bpy.types.Scene.mt_tile_y
        del bpy.types.Scene.mt_tile_z
        del bpy.types.Scene.mt_base_system
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_system
        del bpy.types.Scene.mt_tile_units
