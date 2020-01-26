import bpy
from bpy.types import Panel


class MT_PT_Display_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Display_Panel"
    bl_label = "Display Settings"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.mt_create_lighting_setup', text="Create lighting Setup")
        layout.prop(scene, 'mt_view_mode')
        if scene.mt_view_mode == 'CYCLES':
            layout.prop(scene, 'mt_use_gpu')
            layout.prop(scene, 'mt_cycles_subdivision_quality')