from bpy.types import Panel


class MT_PT_Tile_Generator_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Main_Panel"
    bl_label = "Make Tile"
    bl_description = "Options to configure the type of tile"

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        obj = context.object
        layout = self.layout

        layout.prop(scene_props, 'mt_tile_blueprint')
        layout.prop(scene_props, 'mt_tile_type')
        layout.prop(scene_props, 'mt_tile_material_1', text="Main Material")
        layout.prop(scene_props, 'mt_UV_island_margin')

        layout.operator('scene.make_tile', text="Make Tile")

        if obj is not None and obj.type == 'MESH':

            if obj.mt_object_props.geometry_type == 'PREVIEW':
                layout.operator('scene.mt_make_3d', text='Make 3D')
            if obj.mt_object_props.geometry_type == 'DISPLACEMENT':
                layout.operator(
                    'scene.mt_return_to_preview',
                    text='Return to Preview')


        layout.operator('scene.delete_tiles', text="Delete Tiles")


class MT_PT_Tile_Options_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_description = "Options to configure the dimensions of a tile"

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        blueprint = scene_props.mt_tile_blueprint
        layout = self.layout

        if blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if blueprint == 'OPENLOCK':
            self.draw_openlock_base_panel(context)
            self.draw_openlock_main_part_panel(context)

        if blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

        self.draw_native_subdiv_panel(context)

        layout.label(text='Modifier Subdivisions')
        layout.prop(scene_props, 'mt_subdivisions')

    def draw_plain_base_panel(self, context):
        pass

    def draw_plain_main_part_panel(self, context):
        pass

    def draw_openlock_base_panel(self, context):
        pass

    def draw_openlock_main_part_panel(self, context):
        pass

    def draw_native_subdiv_panel(self, context):
        pass

    def draw_custom_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout
        layout.label(text="Part Blueprints:")

        layout.prop(scene_props, 'mt_base_blueprint')
        layout.prop(scene_props, 'mt_main_part_blueprint')

        if scene_props.mt_base_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)

        if scene_props.mt_base_blueprint == 'OPENLOCK':
            self.draw_openlock_base_panel(context)

        if scene_props.mt_main_part_blueprint == 'PLAIN':
            self.draw_plain_main_part_panel(context)

        if scene_props.mt_main_part_blueprint == 'OPENLOCK':
            self.draw_openlock_main_part_panel(context)


class MT_PT_Straight_Tile_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Straight_Tile_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type in (
            'STRAIGHT_WALL',
            'STRAIGHT_FLOOR',
            'RECTANGULAR_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'mt_base_x')
        row.prop(scene_props, 'mt_base_y')
        row.prop(scene_props, 'mt_base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'mt_tile_x')
        row.prop(scene_props, 'mt_tile_y')
        row.prop(scene_props, 'mt_tile_z')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_main_part_blueprint == 'NONE':
            layout.label(text="Base Size")
            layout.prop(scene_props, 'mt_tile_x')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size:")
        row = layout.row()

        if scene_props.mt_tile_type == 'STRAIGHT_WALL':
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_z')
        else:
            row.prop(scene_props, 'mt_tile_x')
            row.prop(scene_props, 'mt_tile_y')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_x_native_subdivisions')
        layout.prop(scene_props, 'mt_y_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')


class MT_PT_Curved_Tile_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Curved_Tile_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type in (
            'CURVED_WALL',
            'CURVED_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'mt_base_y', text='Base Thickness')
        layout.prop(scene_props, 'mt_base_z', text='Base Height')
        layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
        layout.prop(scene_props, 'mt_degrees_of_arc', text="Degrees of Arc")

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'mt_tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_tile_type == 'CURVED_WALL':
            layout.prop(scene_props, 'mt_wall_radius', text='Wall Radius')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_degrees_of_arc', text="Degrees of Arc")
            layout.prop(scene_props, 'mt_base_radius', text="Base Radius")

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties:")
        layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
        layout.prop(scene_props, 'mt_degrees_of_arc', text="Degrees of Arc")
        layout.prop(scene_props, 'mt_base_socket_side')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_base_radius', text="Tile Radius")
            layout.prop(scene_props, 'mt_degrees_of_arc', text="Degrees of Arc")

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_curve_native_subdivisions')
        layout.prop(scene_props, 'mt_y_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')


class MT_PT_L_Tiles_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_L_Tiles_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type in (
            'CORNER_WALL',
            'CORNER_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'mt_base_y', text='Base Thickness')
        layout.prop(scene_props, 'mt_base_z', text='Base Height')
        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'mt_tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_leg_1_native_subdivisions')
        layout.prop(scene_props, 'mt_leg_2_native_subdivisions')
        layout.prop(scene_props, 'mt_width_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')


class MT_PT_U_Tiles_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_U_Tiles_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type in (
            'U_WALL')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'mt_base_y', text='Base Thickness')
        layout.prop(scene_props, 'mt_base_z', text='Base Height')
        layout.prop(scene_props, 'mt_tile_x', text='End Wall Length')
        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'mt_tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_tile_x', text='End Wall Length')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'mt_tile_x', text='End Wall Length')
        layout.prop(scene_props, 'mt_base_socket_side', text='Base Socket Side')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_tile_x', text='End Wall Length')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")

        layout.prop(scene_props, 'mt_leg_1_native_subdivisions')
        layout.prop(scene_props, 'mt_leg_2_native_subdivisions')
        layout.prop(scene_props, 'mt_x_native_subdivisions')
        layout.prop(scene_props, 'mt_width_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')


class MT_PT_Semi_Circ_Tiles_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Semi_Circ_Tiles_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type == 'SEMI_CIRC_FLOOR'

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'mt_base_z', text='Base Height')
        layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
        layout.prop(scene_props, 'mt_angle', text="Angle")
        layout.prop(scene_props, 'mt_curve_type', text="Curve Type")

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_base_radius', text="Radius")
            layout.prop(scene_props, 'mt_angle', text="Angle")
            layout.prop(scene_props, 'mt_curve_type', text="Curve Type")

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties:")
        layout.prop(scene_props, 'mt_base_radius', text="Base Radius")
        layout.prop(scene_props, 'mt_angle', text="Angle")
        layout.prop(scene_props, 'mt_curve_type', text="Curve Type")

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_base_blueprint == 'NONE':
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'mt_base_radius', text="Radius")
            layout.prop(scene_props, 'mt_angle', text="Angle")
            layout.prop(scene_props, 'mt_curve_type', text="Curve Type")

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_x_native_subdivisions')
        layout.prop(scene_props, 'mt_y_native_subdivisions')
        layout.prop(scene_props, 'mt_z_native_subdivisions')
        layout.prop(scene_props, 'mt_curve_native_subdivisions')


class MT_PT_Triangular_Tiles_Options_Panel(MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Triangular_Tiles_Options'

    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.mt_tile_type == 'TRIANGULAR_FLOOR'

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'mt_base_z', text='Base Height')
        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'mt_tile_z', text='Tile Height')

        if scene_props.mt_base_blueprint == 'NONE':
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.mt_base_blueprint == 'NONE':
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'mt_leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'mt_leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'mt_angle', text='Angle')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'mt_opposite_native_subdivisions', text='Sides')
        layout.prop(scene_props, 'mt_z_native_subdivisions')


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
        return obj and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Convert Object")
        layout.operator('object.convert_to_make_tile', text='Convert to MakeTile Object')

        layout.label(text="Flatten Object")
        layout.operator('object.flatten_tiles', text="Flatten Selected Tiles")

        layout.label(text="Add selected to Tile")
        layout.operator('object.add_to_tile', text="Add Selected to Tile")
        layout.prop(scene, "mt_apply_modifiers")
