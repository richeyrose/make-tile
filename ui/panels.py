import bpy
import os

class MT_PT_Panel(bpy.types.Panel):
    bl_idname       = "MT_PT_Panel"
    bl_label        = "Make Tiles"
    bl_category     = "Make-Tile"
    bl_space_type   = "View_3D"
    bl_region_type  = "UI"

    def draw(self, context):
        scn = context.scene
        lay = self.layout
        lay.operator('scene.make_tile', text="Make Tile")
        lay.prop(scn, 'tile_name')
        lay.prop(scn, 'tile_system')
        lay.prop(scn, 'tile_type')
        lay.prop(scn, 'base_size')
        lay.prop(scn, 'tile_size')