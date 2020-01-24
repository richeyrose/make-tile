import bpy
from bpy.types import Panel


class MT_PT_Voxelise_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.voxelise_tile', text='Voxelise Tile')
        layout.prop(scene, 'mt_voxel_quality')
        layout.prop(scene, 'mt_voxel_adaptivity')
        layout.prop(scene, 'mt_merge_and_voxelise')


class MT_PT_Trim_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Trim_Panel"
    bl_label = "Trim Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        obj = context.object
        obj_props = obj.mt_object_props
        tile_name = obj_props.tile_name
        tile_collection = bpy.data.collections[tile_name]
        tile_props = tile_collection.mt_tile_props

        if tile_props.is_mt_collection is True:
            tile_name = tile_props.tile_name

            for item in tile_props.trimmers_collection:
                seperator = '.'
                stripped_name = item.name.split(seperator, 1)[0]
                layout.prop(item, "value", text=stripped_name)
        layout.operator('object.convert', text="Flatten Selected Object")


class MT_PT_Export_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Export_Panel"
    bl_label = "Export"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.export_tile', text='Export Tile')
        layout.prop(scene, 'mt_export_path')

        row = layout.row()
        layout.prop(scene, 'mt_units')
        layout.prop(scene, 'mt_voxelise_on_export')
        layout.prop(scene, 'mt_num_variants')
