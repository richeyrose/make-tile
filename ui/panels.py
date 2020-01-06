import os
import bpy
from bpy.types import Menu, Panel, UIList


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
        obj = context.object

        if scene.mt_tile_type == 'STRAIGHT_WALL':
            layout.label(text="Tile Size:")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_z')

            if obj is not None and obj.type == 'MESH':
                layout.label(text="Side Sockets:")
                for item in obj.mt_object_props.cutters_collection:
                    row = layout.row()
                    row.prop(item, "value", text=item.name)

        elif scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Tile Properties:")
            layout.prop(scene, 'mt_wall_radius')
            layout.prop(scene, 'mt_degrees_of_arc')
            layout.prop(scene, 'mt_segments')
            '''
            layout.label(text="Base Properties")
            layout.prop(scene, 'mt_base_socket_side')
            '''
            layout.label(text="Wall Height")
            layout.prop(scene, 'mt_tile_z')

            if obj is not None and obj.type == 'MESH':
                layout.label(text="Side Sockets:")
                for item in obj.mt_object_props.cutters_collection:
                    row = layout.row()
                    row.prop(item, "value", text=item.name)

        elif scene.mt_tile_type == 'CORNER_WALL':
            layout.label(text="Wall Height")
            row = layout.row()
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

            if obj is not None and obj.type == 'MESH':
                layout.label(text="Side Sockets:")
                for item in obj.mt_object_props.cutters_collection:
                    seperator = '.'
                    stripped_name = item.name.split(seperator, 1)[0]
                    row = layout.row()
                    row.prop(item, "value", text=stripped_name)

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')

        elif scene.mt_tile_type == 'TRIANGULAR_FLOOR':
            layout.label(text="Tile Properties:")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

        elif scene.mt_tile_type == 'CURVED_FLOOR':
            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_base_radius', text="Straight edge length")
            layout.prop(scene, 'mt_angle_1', text="Degrees of arc")
            layout.prop(scene, 'mt_curve_type')
            layout.prop(scene, 'mt_segments')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        layout = self.layout

        if scene.mt_tile_type == 'STRAIGHT_WALL' or scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Base Size")
            row = layout.row()
            row.prop(scene, 'mt_base_x')
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

        if scene.mt_tile_type == 'CORNER_WALL':
            layout.label(text="Base Thickness and Height")
            row = layout.row()
            row.prop(scene, 'mt_base_y')
            row.prop(scene, 'mt_base_z')

        if scene.mt_tile_type == 'TRIANGULAR_FLOOR':
            layout.label(text="Base Height")
            row = layout.row()
            row.prop(scene, 'mt_base_z')

            layout.label(text="Tile Height")
            row = layout.row()
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

        if scene.mt_tile_type == 'CURVED_FLOOR':
            layout.label(text="Base Height")
            layout.prop(scene, 'mt_base_z')

            layout.label(text="Tile Height")
            layout.prop(scene, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_base_radius', text="Straight edge length")
            layout.prop(scene, 'mt_angle_1', text="Degrees of arc")
            layout.prop(scene, 'mt_curve_type')
            layout.prop(scene, 'mt_segments')

        if scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Base Properties")
            layout.prop(scene, 'mt_base_radius')
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

        elif scene.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene, 'mt_tile_x')
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

        elif scene.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Tile Properties")
            layout.prop(scene, 'mt_wall_radius')
            layout.prop(scene, 'mt_degrees_of_arc')
            layout.prop(scene, 'mt_segments')

            layout.label(text="Wall Thickness and Height")
            row = layout.row()
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

        elif scene.mt_tile_type == 'CORNER_WALL':

            layout.label(text="Wall thickness and height")
            row = layout.row()
            row.prop(scene, 'mt_tile_y')
            row.prop(scene, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene, 'mt_x_leg_len')
            layout.prop(scene, 'mt_y_leg_len')
            layout.prop(scene, 'mt_angle_1')

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


class MT_PT_Vertex_Groups_Panel(MT_PT_Panel, bpy.types.Panel):
    bl_label = "Vertex Groups"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        engine = context.engine
        obj = context.object
        return (obj and obj.type in {'MESH'} and (engine in cls.COMPAT_ENGINES))

    def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.vertex_groups.active

        # number of rows to show
        rows = 3
        if group:
            rows = 5

        row = layout.row()
        row.template_list("MESH_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)
        col = row.column(align=True)

        col.operator("object.vertex_group_add", icon='ADD', text="")
        props = col.operator("object.vertex_group_remove", icon='REMOVE', text="")
        props.all_unlocked = props.all = False

        col.separator()

        col.menu("MESH_MT_vertex_group_context_menu", icon='DOWNARROW_HLT', text="")

        if group:
            col.separator()
            col.operator("object.vertex_group_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if ob.vertex_groups and ob.mode == 'EDIT':
            row = layout.row()

            sub = row.row(align=True)
            sub.operator("object.vertex_group_assign", text="Assign")
            sub.operator("object.vertex_group_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.operator("object.vertex_group_select", text="Select")
            sub.operator("object.vertex_group_deselect", text="Deselect")

            layout.prop(context.tool_settings, "vertex_group_weight", text="Weight")

        if ob.vertex_groups and ob.mode == 'OBJECT' and ob.type == 'MESH':
            row = layout.row()
            row.operator("object.assign_mat_to_active_vert_group", text="Assign Material")
            row.operator("object.remove_mat_from_active_vert_group", text="Remove Material")


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

        tile_collection = context.collection

        tile_props = tile_collection.mt_tile_props

        if tile_props.is_mt_collection is True:
            tile_name = tile_props.tile_name

            for item in tile_props.trimmers_collection:
                seperator = '.'
                stripped_name = item.name.split(seperator, 1)[0]
                layout.prop(item, "value", text=stripped_name)


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
        layout.prop(scene, 'mt_trim_on_export')


class MT_PT_Converter_Panel(MT_PT_Panel, bpy.types.Panel):
    '''Allows you to convert any mesh object into a MakeTile object'''
    bl_idname = "MT_PT_Panel"
    bl_label = "Object Converter"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        layout.operator('object.convert_to_make_tile', text='Convert object')
