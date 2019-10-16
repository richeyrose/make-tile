import bpy
import os
from .. utils.create import make_tile

class MT_OT_makeTile(bpy.types.Operator):
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"

    def execute(self, context):
        make_tile(
            tile_system = context.scene.mt_tile_system, 
            tile_type = context.scene.mt_tile_type, 
            tile_size = context.scene.mt_tile_size, 
            base_size = context.scene.mt_base_size,
        )

        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        #Menus for EnumProperty's
        tile_systems = [
            ("OPENLOCK", "OpenLOCK", "", 1),
            ("PLAIN", "Plain", "", 2),
        ]

        tile_types = [
            ("WALL", "Wall", "", 1),
            ("FLOOR", "Floor", "", 2),
        ]

        bpy.types.Scene.mt_tile_system = bpy.props.EnumProperty(
            items = tile_systems,
            name = "Tile System",
            default = "OPENLOCK",
        )

        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items = tile_types,
            name = "Tile Type",
            default = "WALL",
        )

        bpy.types.Scene.mt_tile_size = bpy.props.FloatVectorProperty(
            name = "Tile Size",
            default = (2.0, 0.5, 2.0),
            subtype = 'XYZ', # see if we can add an enum of Width, thickness, height
            size = 3,
            precision = 3,            
        )

        bpy.types.Scene.mt_base_size = bpy.props.FloatVectorProperty(
            name = "Base Size",
            default = (2.0, 0.5, 0.3),
            subtype = 'XYZ', # see if we can add an enum of Width, thickness, height
            size = 3,
            precision = 3,            
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_base_size
        del bpy.types.Scene.mt_tile_size
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_system