import bpy
from bpy.types import Panel


class MT_PT_Tile_Generator_Panel(Panel):
    """The main tile generation panel.

    Args:
        Panel (bpy.types.Panel): Panel parent class
    """

    bl_order = 0
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Tile_Generator_Panel"
    bl_label = "MakeTile"
    bl_description = "The main tile generation panel."

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        obj = context.active_object
        layout = self.layout

        layout.prop(scene_props, 'tile_type_new')
        layout.prop(scene_props, 'tile_material_1', text="Main Material")
        layout.prop(scene_props, 'UV_island_margin')
        layout.operator(scene_props.tile_type_new, text="MakeTile")

        if obj is not None and obj.type == 'MESH':
            if obj.mt_object_props.geometry_type == 'PREVIEW':
                layout.operator('scene.mt_make_3d', text='Make 3D')
            if obj.mt_object_props.geometry_type == 'DISPLACEMENT':
                layout.operator(
                    'scene.mt_return_to_preview',
                    text='Return to Preview')

        layout.operator('scene.delete_tiles', text="Delete Tiles")


'''
class MT_PT_Tile_Generator_Panel(Panel):
    bl_order = 0
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

        layout.prop(scene_props, 'tile_blueprint')
        layout.prop(scene_props, 'tile_type')
        layout.prop(scene_props, 'tile_material_1', text="Main Material")
        layout.prop(scene_props, 'UV_island_margin')

        #layout.operator('scene.make_tile', text="Make Tile")

        if obj is not None and obj.type == 'MESH':

            if obj.mt_object_props.geometry_type == 'PREVIEW':
                layout.operator('scene.mt_make_3d', text='Make 3D')
            if obj.mt_object_props.geometry_type == 'DISPLACEMENT':
                layout.operator(
                    'scene.mt_return_to_preview',
                    text='Return to Preview')


        layout.operator('scene.delete_tiles', text="Delete Tiles")
'''
'''
class MT_PT_Tile_Options_Panel():
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Tile Options"
    bl_description = "Options to configure the dimensions of a tile"

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        blueprint = scene_props.tile_blueprint
        layout = self.layout

        if blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if blueprint == 'OPENLOCK':
            self.draw_openlock_base_panel(context)
            self.draw_openlock_main_part_panel(context)

        if blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

        # self.draw_native_subdiv_panel(context)

        layout.label(text='Modifier Subdivisions')
        layout.prop(scene_props, 'subdivisions')

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

        layout.prop(scene_props, 'base_blueprint')
        layout.prop(scene_props, 'main_part_blueprint')

        if scene_props.base_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)

        if scene_props.base_blueprint == 'OPENLOCK':
            self.draw_openlock_base_panel(context)

        if scene_props.main_part_blueprint == 'PLAIN':
            self.draw_plain_main_part_panel(context)

        if scene_props.main_part_blueprint == 'OPENLOCK':
            self.draw_openlock_main_part_panel(context)
'''

class MT_PT_Openlock_Socket_Panel(bpy.types.Panel):
    bl_order = 3
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Sockets"
    bl_description = "Openlock Sockets"

    @classmethod
    def poll(cls, context):

        if len(context.selected_objects) > 0:
            obj = context.object
            if obj is not None and obj.type == 'MESH':
                if obj.mt_object_props.is_mt_object and obj.mt_object_props.geometry_type in ('PREVIEW', 'DISPLACEMENT'):
                    tile_name = obj.mt_object_props.tile_name
                    tile = bpy.data.collections[tile_name]
                    tile_props = tile.mt_tile_props
                    main_part_blueprint = tile_props.main_part_blueprint
                    if main_part_blueprint == 'OPENLOCK':
                        return True
        return False

    def draw(self, context):
        obj = context.object
        layout = self.layout

        for cutter in obj.mt_object_props.cutters_collection:
            seperator = '.'
            stripped_name = cutter.name.split(seperator, 1)[0]
            layout.prop(cutter, "value", text=stripped_name)

'''
class MT_PT_Connecting_Column_Tile_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Connecting_Column_Tile_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type == 'CONNECTING_COLUMN'

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_y')
        row.prop(scene_props, 'tile_z')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size:")
        layout.prop(scene_props, 'tile_z', text='Tile Height')


class MT_PT_Straight_Tile_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Straight_Tile_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type in (
            'STRAIGHT_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Size")
        row = layout.row()
        row.prop(scene_props, 'base_x')
        row.prop(scene_props, 'base_y')
        row.prop(scene_props, 'base_z')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size")
        row = layout.row()
        row.prop(scene_props, 'tile_x')
        row.prop(scene_props, 'tile_y')
        row.prop(scene_props, 'tile_z')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.main_part_blueprint == 'NONE':
            layout.label(text="Base Size")
            layout.prop(scene_props, 'tile_x')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Size:")
        row = layout.row()

        if scene_props.tile_type == 'STRAIGHT_WALL':
            row.prop(scene_props, 'tile_x')
            row.prop(scene_props, 'tile_z')
        else:
            row.prop(scene_props, 'tile_x')
            row.prop(scene_props, 'tile_y')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'x_native_subdivisions')
        layout.prop(scene_props, 'y_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')


class MT_PT_Curved_Tile_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Curved_Tile_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type in (
            'CURVED_WALL',
            'CURVED_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_y', text='Base Thickness')
        layout.prop(scene_props, 'base_z', text='Base Height')
        layout.prop(scene_props, 'base_radius', text="Base Radius")
        layout.prop(scene_props, 'degrees_of_arc', text="Degrees of Arc")

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.tile_type == 'CURVED_WALL':
            layout.prop(scene_props, 'wall_radius', text='Wall Radius')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'degrees_of_arc', text="Degrees of Arc")
            layout.prop(scene_props, 'base_radius', text="Base Radius")

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties:")
        layout.prop(scene_props, 'base_radius', text="Base Radius")
        layout.prop(scene_props, 'degrees_of_arc', text="Degrees of Arc")
        layout.prop(scene_props, 'base_socket_side')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'base_radius', text="Tile Radius")
            layout.prop(scene_props, 'degrees_of_arc', text="Degrees of Arc")

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'curve_native_subdivisions')
        layout.prop(scene_props, 'y_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')


class MT_PT_L_Tiles_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_L_Tiles_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type in (
            'CORNER_WALL',
            'CORNER_FLOOR')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'base_y', text='Base Thickness')
        layout.prop(scene_props, 'base_z', text='Base Height')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'angle', text='Angle')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'angle', text='Angle')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'leg_1_native_subdivisions')
        layout.prop(scene_props, 'leg_2_native_subdivisions')
        layout.prop(scene_props, 'width_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')


class MT_PT_U_Tiles_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_U_Tiles_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type in (
            'U_WALL')

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'base_y', text='Base Thickness')
        layout.prop(scene_props, 'base_z', text='Base Height')
        layout.prop(scene_props, 'tile_x', text='End Wall Length')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_y', text='Tile Thickness')
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'tile_x', text='End Wall Length')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")

        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'tile_x', text='End Wall Length')
        layout.prop(scene_props, 'base_socket_side', text='Base Socket Side')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties:")
        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'tile_x', text='End Wall Length')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")

        layout.prop(scene_props, 'leg_1_native_subdivisions')
        layout.prop(scene_props, 'leg_2_native_subdivisions')
        layout.prop(scene_props, 'x_native_subdivisions')
        layout.prop(scene_props, 'width_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')


class MT_PT_Semi_Circ_Tiles_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Semi_Circ_Tiles_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type == 'SEMI_CIRC_FLOOR'

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text='Base Height')
        layout.prop(scene_props, 'base_radius', text="Base Radius")
        layout.prop(scene_props, 'angle', text="Angle")
        layout.prop(scene_props, 'curve_type', text="Curve Type")

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'base_radius', text="Radius")
            layout.prop(scene_props, 'angle', text="Angle")
            layout.prop(scene_props, 'curve_type', text="Curve Type")

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties:")
        layout.prop(scene_props, 'base_radius', text="Base Radius")
        layout.prop(scene_props, 'angle', text="Angle")
        layout.prop(scene_props, 'curve_type', text="Curve Type")

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.base_blueprint == 'NONE':
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'base_radius', text="Radius")
            layout.prop(scene_props, 'angle', text="Angle")
            layout.prop(scene_props, 'curve_type', text="Curve Type")

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'x_native_subdivisions')
        layout.prop(scene_props, 'y_native_subdivisions')
        layout.prop(scene_props, 'z_native_subdivisions')
        layout.prop(scene_props, 'curve_native_subdivisions')


class MT_PT_Triangular_Tiles_Options_Panel(bpy.types.Panel, MT_PT_Tile_Options_Panel):
    bl_idname = 'MT_PT_Triangular_Tiles_Options'
    bl_order = 2
    @classmethod
    def poll(cls, context):
        return context.scene.mt_scene_props.tile_type == 'TRIANGULAR_FLOOR'

    def draw_plain_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'base_z', text='Base Height')
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

    def draw_plain_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Tile Properties")

        layout.prop(scene_props, 'tile_z', text='Tile Height')

        if scene_props.base_blueprint == 'NONE':
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'angle', text='Angle')

    def draw_openlock_base_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Base Properties")
        layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
        layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
        layout.prop(scene_props, 'angle', text='Angle')

    def draw_openlock_main_part_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        if scene_props.base_blueprint == 'NONE':
            layout.label(text="Tile Properties:")
            layout.prop(scene_props, 'leg_1_len', text='Leg 1 Length')
            layout.prop(scene_props, 'leg_2_len', text='Leg 2 Length')
            layout.prop(scene_props, 'angle', text='Angle')

    def draw_native_subdiv_panel(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.label(text="Native Subdivisions:")
        layout.prop(scene_props, 'opposite_native_subdivisions', text='Sides')
        layout.prop(scene_props, 'z_native_subdivisions')
'''

class MT_PT_Converter_Panel(Panel):
    '''Allows you to convert any mesh object into a MakeTile object'''
    bl_order = 9
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
        scene_props = scene.mt_scene_props

        layout.label(text="Rescale Object")
        row = layout.row()
        row.prop(scene_props, 'base_unit', text="Tile Unit")

        layout.operator('object.mt_rescale_object')

        layout.label(text="Convert Object")
        layout.operator('object.convert_to_make_tile', text='Convert to MakeTile Object')

        layout.label(text="Flatten Object")
        layout.operator('object.flatten_tiles', text="Flatten Selected Tiles")

        layout.label(text="Add selected to Tile")
        layout.operator('object.add_to_tile', text="Add Selected to Tile")
        layout.prop(scene, "mt_apply_modifiers")
