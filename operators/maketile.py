"""Contains operator class to make tiles"""
import bpy
from mathutils import Vector
from .. tile_creation.create_tile import make_tile
from .. enums.enums import tile_systems, tile_types, units, base_types
from .. utils.registration import get_prefs

class MT_OT_Make_Tile(bpy.types.Operator):
    """Operator class used to create tiles"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"

    def execute(self, context):

        tile_system = context.scene.mt_tile_system
        tile_type = context.scene.mt_tile_type
        tile_size = context.scene.mt_tile_size
        bhas_base = context.scene.mt_bhas_base
        base_size = context.scene.mt_base_size
        tile_units = context.scene.mt_tile_units
        base_system = context.scene.mt_base_system

        if tile_system == 'OPENLOCK':
            tile_units = 'IMPERIAL'
            bhas_base = True
            base_system = 'OPENLOCK'
            base_size = Vector((tile_size[0], 0.5, 0.3))

        if tile_units == 'IMPERIAL':
            tile_size = tile_size * 2.54
            base_size = base_size * 2.54
            
        if not bhas_base:
            base_size = Vector((0,0,0))
        
        make_tile(
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
            default="WALL",
        )
        
        bpy.types.Scene.mt_base_system = bpy.props.EnumProperty(
            items=base_types,
            name="Base Types",
            default=preferences.default_base_system,
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

        bpy.types.Scene.mt_bhas_base = bpy.props.BoolProperty(
            name="Seperate Base",
            description="Does this tile have a seperate base?",
            default=preferences.default_bhas_base,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_bhas_base
        del bpy.types.Scene.mt_base_size
        del bpy.types.Scene.mt_tile_size
        del bpy.types.Scene.mt_base_system
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_system
        del bpy.types.Scene.mt_tile_units