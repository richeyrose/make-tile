import bpy
from bpy.types import Panel

class MT_PT_Material_Slots_Panel(Panel):
    bl_order = 5
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Materials"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj is not None)

    def draw(self, context):
        layout = self.layout

        obj = context.object
        space = context.space_data

        if obj:
            is_sortable = len(obj.material_slots) > 1
            rows = 3
            if is_sortable:
                rows = 5

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", obj, "material_slots", obj, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            layout.template_ID(obj, "active_material")

            row = layout.row()
            row.operator('material.mt_copy', text="Duplicate Material")
            row.operator('material.mt_export_material', text='Save Material')


class MT_PT_Material_Options_Panel(Panel):
    bl_order = 7
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Material_Options_Panel"
    bl_label = "Material Options"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # TODO only show in preview mode
        obj = context.object
        if obj is not None:
            mat = obj.active_material
            return mat is not None
        return False

    def draw(self, context):
        scene_props = context.scene.mt_scene_props
        layout = self.layout
        # TODO check that changing tile resolution in menu actuallly changes it.
        # layout.prop(scene_props, 'tile_resolution')
        layout.prop(scene_props, 'displacement_strength')
        obj = context.object
        material = obj.active_material
        tree = material.node_tree
        nodes = tree.nodes

        # search for a custom image node and add a load image section
        if 'mt_custom_image' in nodes:
            layout.label(text="Custom Image")
            image_node = nodes['mt_custom_image']
            layout.template_ID(image_node, "image", new="image.new", open="image.open")
            layout.prop(image_node, "extension", text="Tiling")

        # search for surface shader node and add colour picker
        if 'surface_shader' in nodes:
            ss_node = nodes['surface_shader']
            color_input = ss_node.inputs[0]
            layout.template_node_view(tree, ss_node, color_input)

        # get all frame nodes in material that are within the 'editable_inputs' frame
        frame_names = []
        if 'editable_inputs' in nodes:
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

        layout.operator('material.gridify')
        layout.operator('material.ungridify')


class MT_PT_Material_Mapping_Options_Panel(Panel):
    bl_order = 8
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Material_Mapping_Panel"
    bl_label = "Material Mapping"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is not None:
            return obj
        return False

    def draw(self, context):
        scene_props = context.scene.mt_scene_props
        layout = self.layout
        obj = context.object

        layout.prop(scene_props, 'material_mapping_method')
        if scene_props.material_mapping_method == 'WRAP_AROUND':
            layout.prop(context.window_manager.mt_radio_buttons, 'mapping_axis', expand=True)

        try:
            material = obj.active_material
            tree = material.node_tree
            text_coord_nodes = [node for node in tree.nodes if node.type == 'TEX_COORD']
            for node in text_coord_nodes:
                if node.parent.name == 'Root Nodes':
                    layout.label(text='Reference Object')
                    layout.prop(node, "object", text="")
        except AttributeError:
            pass


class MT_PT_Vertex_Groups_Panel(bpy.types.Panel):
    bl_order = 6
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Textured Areas"
    COMPAT_ENGINES = {'CYCLES', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

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
            row.operator("object.mt_assign_mat_to_active_vert_group", text="Assign Material")
            row.operator("object.mt_remove_mat_from_active_vert_group", text="Remove Material")
