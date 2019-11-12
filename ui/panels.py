import os
import bpy


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

        if scene.mt_tile_system == 'OPENLOCK':
            if scene.mt_tile_type == 'WALL':
                layout.row()
                layout.prop(scene, 'mt_tile_x')
                layout.prop(scene, 'mt_tile_z')
            elif scene.mt_tile_type == 'FLOOR':
                layout.row()
                layout.prop(scene, 'mt_tile_x')
                layout.prop(scene, 'mt_tile_y')

        if scene.mt_tile_system == 'CUSTOM':
            layout.prop(scene, 'mt_tile_units')

            if scene.mt_tile_type == 'WALL' or 'FLOOR':
                layout.row()
                layout.prop(scene, 'mt_tile_x')
                layout.prop(scene, 'mt_tile_y')
                layout.prop(scene, 'mt_tile_z')

                layout.row()
                layout.prop(scene, 'mt_bhas_base')

                if scene.mt_bhas_base:
                    layout.row()
                    layout.prop(scene, 'mt_base_x')
                    layout.prop(scene, 'mt_base_y')
                    layout.prop(scene, 'mt_base_z')
