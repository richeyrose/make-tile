import bpy
from bpy.types import Panel


class MT_PT_Voxelise_Panel(Panel):
    bl_order = 9
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.mt_voxelise_objects', text='Voxelise Objects')
        layout.prop(scene, 'mt_voxel_size')
        layout.prop(scene, 'mt_voxel_adaptivity')
        layout.prop(scene, 'mt_merge')


class MT_PT_Export_Panel(Panel):
    bl_order = 10
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Export_Panel"
    bl_label = "Export"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.mt_export_tile', text='Export Tile')
        layout.prop(scene, 'mt_export_path')
        layout.prop(scene, 'mt_units')
        layout.prop(scene, 'mt_voxelise_on_export')
        layout.prop(scene, 'mt_randomise_on_export')

        if scene.mt_randomise_on_export is True:
            layout.prop(scene, 'mt_num_variants')
