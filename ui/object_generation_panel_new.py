import os
import json
import bpy
from .. utils.registration import get_prefs

class MT_PT_Object_Generator_Panel(bpy.types.Panel):
    bl_order = 0
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Object_Generator_Panel"
    bl_label = "Make Tile"

    def draw(self, context):
        scene = context.scene
        factory_props = scene.mt_object_factory_props
        layout = self.layout
        layout.prop(factory_props, 'template_types')


class MT_Object_Factory_Properties(bpy.types.PropertyGroup):
    def create_template_enums(self, context):
        prefs = get_prefs()

        object_defaults = os.path.join(
            prefs.assets_path,
            "object_definitions",
            "object_defaults.json"
        )

        enum_items = []

        with open(object_defaults) as json_file:
            data = json.load(json_file)
            for i in data['ObjectTypes']:
                if i['ParentType'] == "Template":
                    enum = (i["Type"], i["Type"], "")
                    enum_items.append(enum)

        return enum_items

    template_types: bpy.props.EnumProperty(
        items=create_template_enums,
        name="Templates"
    )

def register():
    bpy.types.Scene.mt_object_factory_props = bpy.props.PointerProperty(
        type=MT_Object_Factory_Properties
    )

def unregister():
    del bpy.types.Scene.mt_object_factory_props
