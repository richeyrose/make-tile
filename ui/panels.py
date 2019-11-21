import os
import bpy


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
        layout.prop(scene, 'mt_tile_blueprint')

        layout.prop(scene, 'mt_tile_type')

        if scene.mt_tile_blueprint == 'PLAIN':
            self.draw_plain_base_panel(context)
            self.draw_plain_main_part_panel(context)

        if scene.mt_tile_blueprint == 'OPENLOCK':
            self.draw_openlock_panel(context)

        if scene.mt_tile_blueprint == 'CUSTOM':
            self.draw_custom_panel(context)

        layout.prop(scene, 'mt_tile_material')

        if bpy.context.object is not None:
            if bpy.context.object['geometry_type'] == 'PREVIEW':
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
        layout.prop(scene, 'mt_base_system')
        layout.prop(scene, 'mt_tile_main_system')

        # TODO: Find out way of setting x y z defaults here.

        if scene.mt_base_system == 'PLAIN':
            self.draw_plain_base_panel(context)
        if scene.mt_tile_main_system == 'PLAIN':
            self.draw_plain_main_part_panel(context)
        if scene.mt_tile_main_system == 'OPENLOCK':
            self.draw_openlock_panel(context)
