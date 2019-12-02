import os
import bpy

'''
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
        layout.operator('scene.create_lighting_setup', text="Create Lighting Setup")

        layout.row()
        layout.prop(scene, 'mt_view_mode')

        layout.prop(scene, 'mt_use_gpu')
        layout.prop(scene, 'mt_cycles_subdivision_quality')

        layout.prop(scene, 'mt_tile_blueprint')

        layout.prop(scene, 'mt_tile_type')

        if scene.mt_tile_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if scene.mt_tile_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)

        if scene.mt_tile_blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

        # TODO: Neaten this up - too many ifs!
        if bpy.context.object is not None:
            if 'geometry_type' in bpy.context.object:
                if bpy.context.object['geometry_type'] == 'PREVIEW':
                    layout.prop(scene, 'mt_tile_material')
                    layout.prop(scene, 'mt_tile_resolution')
                    input_nodes = get_material_inputs(context)
                    if input_nodes is not None:
                        for node in input_nodes:
                            layout.prop(node.outputs['Value'], 'default_value', text=node.name)
                    layout.operator('scene.bake_displacement', text='Make 3D')
                if bpy.context.object['geometry_type'] == 'DISPLACEMENT':
                    layout.operator('scene.return_to_preview', text='Return to Preview')

    def draw_openlock_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.row()
            layout.prop(scene, 'mt_tile_x')
            layout.prop(scene, 'mt_tile_z')

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.row()
            layout.prop(scene, 'mt_tile_x')
            layout.prop(scene, 'mt_tile_y')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or 'RECTANGULAR_FLOOR':
            layout.prop(scene, 'mt_base_x')
            layout.prop(scene, 'mt_base_y')
            layout.prop(scene, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or 'RECTANGULAR_FLOOR':
            layout.prop(scene, 'mt_tile_x')
            layout.prop(scene, 'mt_tile_y')
            layout.prop(scene, 'mt_tile_z')

    def draw_custom_panel(self, context):
        scene = context.scene
        layout = self.layout

        layout.row()
        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.prop(scene, 'mt_base_system')
            layout.prop(scene, 'mt_tile_main_system')

            if scene.mt_base_system == 'PLAIN':
                self.draw_plain_base_panel(context)
            if scene.mt_tile_main_system == 'PLAIN':
                self.draw_plain_main_part_panel(context)
            if scene.mt_tile_main_system == 'OPENLOCK':
                self.draw_openlock_panel(context)

        if scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.prop(scene, 'mt_base_system')
            if scene.mt_base_system == 'PLAIN':
                self.draw_plain_base_panel(context)
                self.draw_plain_main_part_panel(context)
            if scene.mt_base_system == 'OPENLOCK':
                self.draw_openlock_panel(context)


def get_material_inputs(context):
    # get all nodes in material that are within the 'editable_inputs' frame
    if context.scene.mt_tile_material in bpy.data.materials:
        material = bpy.data.materials[context.scene.mt_tile_material]
        tree = material.node_tree
        nodes = tree.nodes
        if 'editable_inputs' in nodes:
            inputs_frame = nodes['editable_inputs']
            input_nodes = []
            for node in nodes:
                if node.parent == inputs_frame:
                    input_nodes.append(node)
            return input_nodes
'''


class MT_PT_Panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"


class MT_PT_Main_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Main_Panel"
    bl_label = "Make Tile"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.make_tile', text="Make Tile")
        layout.prop(scene, 'mt_tile_blueprint')
        layout.prop(scene, 'mt_tile_type')

        if scene.mt_tile_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if scene.mt_tile_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)

        if scene.mt_tile_blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

    def draw_openlock_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_z')

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or 'RECTANGULAR_FLOOR':
            layout.label(text="Base Size")
            row = layout.row()
            row.prop(scene, 'mt_base_x')
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

    def draw_custom_panel(self, context):
        scene = context.scene
        layout = self.layout

        layout.row()
        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.prop(scene, 'mt_base_system')
            layout.prop(scene, 'mt_tile_main_system')

            if scene.mt_base_system == 'PLAIN':
                self.draw_plain_base_panel(context)
            if scene.mt_tile_main_system == 'PLAIN':
                self.draw_plain_main_part_panel(context)
            if scene.mt_tile_main_system == 'OPENLOCK':
                self.draw_openlock_panel(context)

        if scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.prop(scene, 'mt_base_system')
            if scene.mt_base_system == 'PLAIN':
                self.draw_plain_base_panel(context)
                self.draw_plain_main_part_panel(context)
            if scene.mt_base_system == 'OPENLOCK':
                self.draw_openlock_panel(context)


class MT_PT_Display_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Display_Panel"
    bl_label = "Display Settings"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.create_lighting_setup', text="Create lighting Setup")
        layout.prop(scene, 'mt_view_mode')
        if scene.mt_view_mode == 'CYCLES':
            layout.prop(scene, 'mt_use_gpu')
            layout.prop(scene, 'mt_cycles_subdivision_quality')


class MT_PT_Material_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Material_Panel"
    bl_label = "Material Settings"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        if bpy.context.object is not None:
            if 'geometry_type' in bpy.context.object:
                if bpy.context.object['geometry_type'] == 'PREVIEW':
                    layout.operator('scene.bake_displacement', text='Make 3D')
                if bpy.context.object['geometry_type'] == 'DISPLACEMENT':
                    layout.operator('scene.return_to_preview', text='Return to Preview')

        layout.prop(scene, 'mt_tile_material')
        layout.prop(scene, 'mt_tile_resolution')
        input_nodes = get_material_inputs(context)
        if input_nodes is not None:
            for node in input_nodes:
                layout.prop(node.outputs['Value'], 'default_value', text=node.name)


class MT_PT_Voxelise_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.voxelise_tile', text='Voxelise Tile')

        layout.prop(scene, 'mt_voxel_quality')
        layout.prop(scene, 'mt_voxel_adaptivity')
        layout.prop(scene, 'mt_merge_and_voxelise')


class MT_PT_Export_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Export_Panel"
    bl_label = "Export Settings"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.export_tile', text='Export Tile')
        layout.prop(scene, 'mt_export_path')

        row = layout.row()
        layout.prop(scene, 'mt_units')
        # TODO: fix merge on export so voxelises properly
        # layout.prop(scene, 'mt_merge_on_export')
        # layout.prop(scene, 'mt_voxelise_on_export')


def get_material_inputs(context):
    # get all nodes in material that are within the 'editable_inputs' frame
    if context.scene.mt_tile_material in bpy.data.materials:
        material = bpy.data.materials[context.scene.mt_tile_material]
        tree = material.node_tree
        nodes = tree.nodes
        if 'editable_inputs' in nodes:
            inputs_frame = nodes['editable_inputs']
            input_nodes = []
            for node in nodes:
                if node.parent == inputs_frame:
                    input_nodes.append(node)
            return input_nodes
