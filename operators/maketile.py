"""Contains operator class to make tiles"""
import bpy
from .. utils.create import make_tile

class MT_OT_Make_Tile(bpy.types.Operator):
    """Operator class used to create tiles"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"

    def execute(self, context):
        tile_system = context.scene.mt_tile_system
        tile_type = context.scene.mt_tile_type
        tile_size = context.scene.mt_tile_size
        base_size = context.scene.mt_base_size
        tile_units = context.scene.mt_tile_units

        if tile_system == 'OPENLOCK':
            tile_units = 'IMPERIAL'
    
        if tile_units == 'IMPERIAL':
            tile_size = tile_size * 2.54
            base_size = (tile_size[0], tile_size[1], 0.3 * 2.54)
        
        make_tile(
            tile_units,
            tile_system,
            tile_type,
            tile_size,
            base_size,
        )

        return {'FINISHED'}
    
    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        #Menus for EnumProperty's
        tile_units = [
            ("METRIC", "Metric", "", 1),
            ("IMPERIAL", "Imperial", "", 2),
        ]

        tile_systems = [
            ("OPENLOCK", "OpenLOCK", "", 1),
            ("CUSTOM", "Custom", "", 2),
        ]

        tile_types = [
            ("WALL", "Wall", "", 1),
            ("FLOOR", "Floor", "", 2),
        ]

        bpy.types.Scene.mt_tile_units = bpy.props.EnumProperty(
            items=tile_units,
            name="Tile Units",
            default="IMPERIAL",
        )
        bpy.types.Scene.mt_tile_system = bpy.props.EnumProperty(
            items=tile_systems,
            name="Tile System",
            default="OPENLOCK",
        )

        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Tile Type",
            default="WALL",
        )

        bpy.types.Scene.mt_tile_size = bpy.props.FloatVectorProperty(
            name="Tile Size",
            default=(2.0, 0.5, 2.0),
            subtype='XYZ', # see if we can add an enum of Width, thickness, height
            size=3,
            precision=3,
        )

        bpy.types.Scene.mt_base_size = bpy.props.FloatVectorProperty(
            name="Base Size",
            default=(2.0, 0.5, 0.3),
            subtype='XYZ', # see if we can add an enum of Width, thickness, height
            size=3,
            precision=3,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_base_size
        del bpy.types.Scene.mt_tile_size
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_system