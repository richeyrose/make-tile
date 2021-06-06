import bpy
from bpy.types import Panel
from bpy.props import BoolProperty, EnumProperty
# TODO create a Layout Mode, Preview Mode switch. Add in a triangulate modifier that can be switched on and off for layout mode.
# Layout mode should also switch everything to 0 subdivision layers and to solid shading
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

        layout.prop(scene_props, 'tile_type')
        layout.prop(scene_props, 'UV_island_margin')
        layout.prop(scene_props, 'subdivisions')

        # Display the appropriate operator based on tile_type
        tile_type = scene_props.tile_type
        tile_defaults = scene_props['tile_defaults']

        for default in tile_defaults:
            if default['type'] == tile_type:
                layout.operator(default['bl_idname'], text="MakeTile")

        if obj is not None and obj.type == 'MESH':
            #if obj.mt_object_props.geometry_type == 'PREVIEW':
            if obj.mt_object_props.is_displacement and obj.mt_object_props.is_displaced is False:
                layout.operator('scene.mt_make_3d', text='Make 3D')
            if obj.mt_object_props.is_displacement and obj.mt_object_props.is_displaced:
                layout.operator(
                    'scene.mt_return_to_preview',
                    text='Return to Preview')

        layout.operator('scene.delete_tiles', text="Delete Tiles")


class MT_PT_Booleans_Panel(bpy.types.Panel):
    """Show a Panel that shows any booleans that can be toggled on the current object."""
    bl_order = 2
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_label = "Booleans"
    bl_description = "Booleans"

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            obj = context.object
            if hasattr(obj, 'mt_object_props'):
                if len(obj.mt_object_props.cutters_collection) > 0:
                    return True
        return False

    def draw(self, context):
        obj = context.object
        layout = self.layout

        for cutter in obj.mt_object_props.cutters_collection:
            seperator = '.'
            stripped_name = cutter.name.split(seperator, 1)[0]
            layout.prop(cutter, "value", text=stripped_name)


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
        layout.prop(scene_props, 'converter_material')
        layout.operator('object.convert_to_make_tile', text='Convert to MakeTile Object')

        layout.label(text="Flatten Object")
        layout.operator('object.flatten_tiles', text="Flatten Selected Tiles")

        layout.label(text="Add selected to Tile")
        layout.operator('object.add_to_tile', text="Add Object to Tile")
        layout.operator('collection.add_collection_to_tile', text="Add Collection to Tile")
