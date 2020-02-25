import bpy
from bpy.types import Panel


class MT_PT_Tile_Generator_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Main_Panel"
    bl_label = "Make Tile"
    bl_description = "Options to configure the type and dimensions of tile"

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.operator('scene.make_tile', text="Make Tile")

        layout.prop(scene_props, 'mt_tile_blueprint')
        layout.prop(scene_props, 'mt_tile_type')
        layout.prop(scene_props, 'mt_tile_material_1', text="Main Material")

        if scene_props.mt_tile_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if scene_props.mt_tile_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)

        if scene_props.mt_tile_blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

        if bpy.context.object is not None:
            if bpy.context.object.mt_object_props.geometry_type == 'PREVIEW':
                layout.operator('scene.mt_make_3d', text='Make 3D')
            if bpy.context.object.mt_object_props.geometry_type == 'DISPLACEMENT':
                layout.operator('scene.mt_return_to_preview', text='Return to Preview')
            layout.prop(scene_props, 'mt_subdivisions')

        layout.operator('scene.delete_tiles', text="Delete Tiles")

    def draw_openlock_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout
        obj = context.object

        if scene_props.mt_tile_type == 'STRAIGHT_WALL':
            layout.label(text="Tile Size:")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_z')

        if scene_props.mt_tile_type == 'STRAIGHT_FLOOR':
            layout.label(text="Tile Size:")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_z')

        if scene_props.mt_tile_type in ('CURVED_WALL', 'CURVED_FLOOR'):
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'mt_base_radius')
            layout.prop(scene_props, 'mt_degrees_of_arc')
            layout.prop(scene_props, 'mt_segments')
            layout.prop(scene_props, 'mt_base_socket_side')
            layout.label(text="Height")
            layout.prop(scene_props, 'mt_tile_z')

        if scene_props.mt_tile_type == 'CORNER_WALL':
            layout.label(text="Wall Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        if scene_props.mt_tile_type == 'CORNER_FLOOR':
            layout.label(text="Floor Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        if scene_props.mt_tile_type == 'RECTANGULAR_FLOOR':
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_y')

        if scene_props.mt_tile_type == 'TRIANGULAR_FLOOR':
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        if scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR':
            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_base_radius', text="Radius")
            layout.prop(scene_props, 'mt_angle', text="Angle")
            layout.prop(scene_props, 'mt_curve_type')
            layout.prop(scene_props, 'mt_segments')

        if scene_props.mt_tile_type == 'STRAIGHT_WALL' or scene_props.mt_tile_type == 'CURVED_WALL' or scene_props.mt_tile_type == 'CORNER_WALL':
            if obj is not None and obj.mt_object_props.is_mt_object is True:
                layout.label(text="Side Sockets:")
                for item in obj.mt_object_props.cutters_collection:
                    seperator = '.'
                    stripped_name = item.name.split(seperator, 1)[0]
                    row = layout.row()
                    row.prop(item, "value", text=stripped_name)

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_tile_type in (
                'STRAIGHT_WALL',
                'RECTANGULAR_FLOOR',
                'STRAIGHT_FLOOR') and \
                scene_props.mt_main_part_blueprint == 'NONE':

            layout.label(text="Base Size")
            row = layout.row()
            row.prop(scene_props, 'mt_base_x')
            row.prop(scene_props, 'mt_base_y')
            row.prop(scene_props, 'mt_base_z')


        if scene_props.mt_tile_type == 'CORNER_WALL' or scene_props.mt_tile_type == 'CORNER_FLOOR':
            layout.label(text="Base Thickness and Height")
            row = layout.row()
            row.prop(scene_props, 'mt_base_y')
            row.prop(scene_props, 'mt_base_z')

        if scene_props.mt_tile_type == 'TRIANGULAR_FLOOR':
            layout.label(text="Base Height")
            row = layout.row()
            row.prop(scene_props, 'mt_base_z')

            layout.label(text="Tile Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        if scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR':
            layout.label(text="Base Height")
            layout.prop(scene_props, 'mt_base_z')

            layout.label(text="Tile Height")
            layout.prop(scene_props, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
            layout.prop(scene_props, 'mt_angle', text="Angle")
            layout.prop(scene_props, 'mt_curve_type')
            layout.prop(scene_props, 'mt_segments')

        if scene_props.mt_tile_type in ('CURVED_WALL', 'CURVED_FLOOR'):
            layout.label(text="Base Properties")
            layout.prop(scene_props, 'mt_base_radius', text="Radius")
            row = layout.row()
            row.prop(scene_props, 'mt_base_y')
            row.prop(scene_props, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_tile_type in (
                'STRAIGHT_WALL',
                'STRAIGHT_FLOOR',
                'RECTANGULAR_FLOOR'):
            layout.label(text="Tile Size")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_y')
            row.prop(scene_props, 'mt_tile_z')

        elif scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR':
            layout.label(text="Tile Height")
            layout.prop(scene_props, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
            layout.prop(scene_props, 'mt_angle', text="Angle")
            layout.prop(scene_props, 'mt_curve_type')
            layout.prop(scene_props, 'mt_segments')

        elif scene_props.mt_tile_type == 'TRIANGULAR_FLOOR':
            layout.label(text="Tile Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        elif scene_props.mt_tile_type == 'CURVED_WALL':
            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_wall_radius')
            layout.prop(scene_props, 'mt_degrees_of_arc')
            layout.prop(scene_props, 'mt_segments')

            layout.label(text="Wall Thickness and Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_y')
            row.prop(scene_props, 'mt_tile_z')

        elif scene_props.mt_tile_type == 'CURVED_FLOOR':
            layout.label(text="Tile Properties")
            layout.prop(scene_props, 'mt_wall_radius', text='Radius')
            layout.prop(scene_props, 'mt_degrees_of_arc')
            layout.prop(scene_props, 'mt_segments')

            layout.label(text="Floor Thickness and Height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_y')
            row.prop(scene_props, 'mt_tile_z')

        elif scene_props.mt_tile_type == 'CORNER_WALL':

            layout.label(text="Wall thickness and height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_y')
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

        elif scene_props.mt_tile_type == 'CORNER_FLOOR':

            layout.label(text="Floor thickness and height")
            row = layout.row()
            row.prop(scene_props, 'mt_tile_y')
            row.prop(scene_props, 'mt_tile_z')

            layout.label(text="Corner Properties")
            layout.prop(scene_props, 'mt_leg_1_len')
            layout.prop(scene_props, 'mt_leg_2_len')
            layout.prop(scene_props, 'mt_angle')

    def draw_custom_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.row()

        layout.prop(scene_props, 'mt_base_blueprint')
        layout.prop(scene_props, 'mt_main_part_blueprint')

        if scene_props.mt_base_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
        if scene_props.mt_base_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)
        if scene_props.mt_main_part_blueprint == 'PLAIN':
            self.draw_plain_main_part_panel(context)
        if scene_props.mt_main_part_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)


class MT_PT_Converter_Panel(Panel):
    '''Allows you to convert any mesh object into a MakeTile object'''
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Panel"
    bl_label = "Object Converter"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def draw(self, context):
        layout = self.layout

        layout.operator('object.convert_to_make_tile', text='Convert to MakeTile Object')
        layout.operator('object.flatten_tiles', text="Flatten Selected Tiles")
        layout.operator('object.add_to_tile', text="Add Selected to Tile")
