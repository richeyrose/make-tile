import os
import bpy


class MT_PT_Panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"


class MT_PT_Main_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Main_Panel"
    bl_label = "Make Tile"
    bl_description = "Options to configure the type and dimensions of tile"

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

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')

        elif scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_wall_inner_radius')
            layout.prop(scene, 'mt_degrees_of_arc')
            layout.prop(scene, 'mt_segments')
            '''
            layout.label(text="Base Properties")
            layout.prop(scene, 'mt_base_socket_side')
            '''
            layout.label(text="Wall Height")
            layout.prop(scene, 'mt_tile_z')

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

        elif scene.mt_tile_type == 'CORNER_WALL':
            layout.label(text="Wall Height")
            row = layout.row()
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Base Size")
            row = layout.row()
            row.prop(scene, 'mt_base_x')
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

        elif scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Base Properties")
            layout.prop(scene, 'mt_base_inner_radius')
            row = layout.row()
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

        elif scene.mt_tile_type == 'CORNER_WALL':
            layout.label(text="Base Thickness and Height")
            row = layout.row()
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

        elif scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_wall_inner_radius')
            layout.prop(scene, 'mt_degrees_of_arc')
            layout.prop(scene, 'mt_segments')

            layout.label(text="Wall Thickness and Height")
            row = layout.row()
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

        elif scene.mt_tile_type == 'CORNER_WALL':

            layout.label(text="Wall thickness and height")
            row = layout.row()
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

            layout.label(text="Textured Sides")
            row = layout.row()
            row.prop(scene, 'mt_x_neg_textured')
            row.prop(scene, 'mt_x_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_y_neg_textured')
            row.prop(scene, 'mt_y_pos_textured')
            row = layout.row()
            row.prop(scene, 'mt_z_neg_textured')
            row.prop(scene, 'mt_z_pos_textured')

    def draw_custom_panel(self, context):
        scene = context.scene
        layout = self.layout

        layout.row()
        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.prop(scene, 'mt_base_blueprint')
            layout.prop(scene, 'mt_main_part_blueprint')

            if scene.mt_base_blueprint == 'PLAIN':
                self.draw_plain_base_panel(context)
            if scene.mt_main_part_blueprint == 'PLAIN':
                self.draw_plain_main_part_panel(context)
            if scene.mt_main_part_blueprint == 'OPENLOCK':
                self.draw_openlock_panel(context)

        if scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.prop(scene, 'mt_base_blueprint')
            if scene.mt_base_blueprint == 'PLAIN':
                self.draw_plain_base_panel(context)
                self.draw_plain_main_part_panel(context)
            if scene.mt_base_blueprint == 'OPENLOCK':
                self.draw_openlock_panel(context)

        if scene.mt_tile_type == 'CURVED_WALL':
            layout.prop(scene, 'mt_base_blueprint')
            layout.prop(scene, 'mt_main_part_blueprint')

            if scene.mt_base_blueprint == 'PLAIN':
                self.draw_plain_base_panel(context)
            if scene.mt_main_part_blueprint == 'PLAIN':
                self.draw_plain_main_part_panel(context)
            if scene.mt_main_part_blueprint == 'OPENLOCK':
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
    bl_label = "Materials"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        if bpy.context.object is not None:
            if 'geometry_type' in bpy.context.object:
                if bpy.context.object['geometry_type'] == 'PREVIEW':
                    layout.operator('scene.bake_displacement', text='Make 3D')
                    layout.prop(scene, 'mt_subdivisions')
                if bpy.context.object['geometry_type'] == 'DISPLACEMENT':
                    layout.operator('scene.return_to_preview', text='Return to Preview')
        layout.prop(scene, 'mt_tile_material_1')


class MT_PT_Material_Options_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Material_Options_Panel"
    bl_label = "Material Options"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.prop(scene, 'mt_tile_resolution')

        if context.scene.mt_tile_material_1 in bpy.data.materials:
            material = bpy.data.materials[context.scene.mt_tile_material_1]
            tree = material.node_tree
            nodes = tree.nodes

            # get all frame nodes in material that are within the 'editable_inputs' frame
            frame_names = []

            for frame in nodes:
                if frame.parent == nodes['editable_inputs']:
                    frame_names.append(frame.name)

            frame_names.sort()
            # Use frame labels as headings in side panel
            for name in frame_names:
                frame = nodes[name]
                layout.label(text=frame.label)

                node_names = []

                # get all nodes in each frame
                for node in nodes:
                    if node.parent == frame:
                        node_names.append(node.name)

                node_names.sort()
                # expose their properties in side panel
                for name in node_names:
                    node = nodes[name]
                    layout.prop(node.outputs['Value'], 'default_value', text=node.label)


class MT_PT_Voxelise_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.voxelise_tile', text='Voxelise Tile')
        layout.prop(scene, 'mt_voxel_quality')
        layout.prop(scene, 'mt_voxel_adaptivity')
        layout.prop(scene, 'mt_merge_and_voxelise')


class MT_PT_Trim_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Trim_Panel"
    bl_label = "Trim Settings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.trim_tile', text='Trim Tile')

        if context.scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            row = layout.row()
            row.prop(scene, 'mt_trim_x_neg')
            row.prop(scene, 'mt_trim_x_pos')
            row = layout.row()
            row.prop(scene, 'mt_trim_y_neg')
            row.prop(scene, 'mt_trim_y_pos')
            row = layout.row()
            row.prop(scene, 'mt_trim_z_neg')
            row.prop(scene, 'mt_trim_z_pos')

        elif context.scene.mt_tile_type == 'STRAIGHT_WALL' or context.scene.mt_tile_type == 'CURVED_WALL':
            row = layout.row()
            row.prop(scene, 'mt_trim_x_neg')
            row.prop(scene, 'mt_trim_x_pos')
            row = layout.row()
            row.prop(scene, 'mt_trim_z_neg')
            row.prop(scene, 'mt_trim_z_pos')

        elif context.scene.mt_tile_type == 'CORNER_WALL':
            layout.prop(scene, 'mt_trim_buffer')
            row = layout.row()
            row.prop(scene, 'mt_trim_x_pos')
            row.prop(scene, 'mt_trim_y_pos')
            row = layout.row()
            row.prop(scene, 'mt_trim_z_neg')
            row.prop(scene, 'mt_trim_z_pos')


class MT_PT_Export_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_idname = "MT_PT_Export_Panel"
    bl_label = "Export Settings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('scene.export_tile', text='Export Tile')
        layout.prop(scene, 'mt_export_path')
        # get collection name / name of tile
        obj = bpy.context.active_object
        if obj is not None:
            tile_collection = obj.users_collection[0]
            layout.prop(tile_collection, "name", text="")

        row = layout.row()
        layout.prop(scene, 'mt_units')
        layout.prop(scene, 'mt_voxelise_on_export')
