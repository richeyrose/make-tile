import bpy
import os

class MT_PT_Panel(bpy.types.Panel):
    bl_idname = "MT_PT_Panel"
    bl_label = "Make Tiles"
    bl_category = "Make-Tile"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.operator('scene.make_tile', text="Make Tile")
        layout.prop(scene, 'mt_tile_system')    
        layout.prop(scene, 'mt_tile_type')
        
        if scene.mt_tile_system == 'CUSTOM':
            layout.prop(scene, 'mt_base_size')
            layout.prop(scene, 'mt_tile_units')

        layout.prop(scene, 'mt_tile_size')
