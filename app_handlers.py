import os
import json
import bpy
from bpy.app.handlers import persistent
from .utils.registration import get_prefs, get_path
from .materials.materials import (
    get_blend_filenames,
    load_materials)


def create_properties_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(create_properties_on_activation)
    create_properties()
    load_material_libraries()


@persistent
def create_properties_on_load(dummy):
    create_properties()
    load_material_libraries()


def load_material_libraries():
    prefs = get_prefs()
    scene_props = bpy.context.scene.mt_scene_props
    default_materials_path = os.path.join(prefs.assets_path, "materials")
    user_materials_path = os.path.join(prefs.user_assets_path, "materials")

    blend_filenames = get_blend_filenames(default_materials_path)
    materials = load_materials(default_materials_path, blend_filenames)

    blend_filenames = get_blend_filenames(user_materials_path)
    materials.extend(load_materials(user_materials_path, blend_filenames))

    scene_props['mt_materials'] = [mat for mat in materials if hasattr(mat, 'mt_material') and mat['mt_material']]


def get_tile_type(tile_type):
    scene = bpy.context.scene
    scene_props = scene.mt_scene_props
    tile_defaults = scene_props['tile_defaults']

    for default in tile_defaults:
        if default['type'] == tile_type:
            return default['type']
    return None

# TODO: Currently using scene_props['tile_defaults'] as a proxy. Should make this more robust
# Blender's undo system also undoes actions triggered by the load_post app handler
# when the appropriate undo step is reached.
# Therefore here we check to see if our tile_defaults custom scene property is being
# unloaded and if it is we rerun create_properties_on_load
@persistent
def recreate_properties_on_undo(dummy):
    context = bpy.context
    scene_props = context.scene.mt_scene_props
    try:
        scene_props['tile_defaults']
    except KeyError:
        create_properties_on_load(dummy)


@persistent
def update_mt_scene_props_handler(dummy):
    """Updates mt_scene_props based on mt_tile_props of selected object.

    This means that when the user selects an existing tile they can easily
    create one with the same properties.
    """
    context = bpy.context
    obj = context.object
    scene_props = context.scene.mt_scene_props

    try:
        obj_props = obj.mt_object_props
        tile_props = bpy.data.collections[obj.mt_object_props.tile_name].mt_tile_props

        if obj != scene_props.mt_last_selected and not obj_props.is_converted and obj_props.is_mt_object:
            scene_props.tile_x = tile_props.tile_size[0]
            scene_props.tile_y = tile_props.tile_size[1]
            scene_props.tile_z = tile_props.tile_size[2]

            scene_props.base_x = tile_props.base_size[0]
            scene_props.base_y = tile_props.base_size[1]
            scene_props.base_z = tile_props.base_size[2]

            for key, value in tile_props.items():
                for k in scene_props.keys():
                    if k == key:
                        scene_props[k] = value
            scene_props.mt_last_selected = obj

    except KeyError:
        pass
    except AttributeError:
        pass


def create_properties():
    context = bpy.context
    load_tile_defaults(context)
    refresh_scene_props(context)
    scene_props = bpy.context.scene.mt_scene_props

    scene_props['mt_materials'] = []  # list of MakeTile compatible displacement materials


def load_tile_defaults(context):
    """Load tile defaults into memory."""
    scene_props = context.scene.mt_scene_props
    addon_path = get_path()
    json_path = os.path.join(
        addon_path,
        "assets",
        "data",
        "tile_defaults.json"
    )

    if os.path.exists(json_path):
        with open(json_path) as json_file:
            tile_defaults = json.load(json_file)
        scene_props['tile_defaults'] = tile_defaults


def refresh_scene_props(context):
    scene_props = context.scene.mt_scene_props
    prefs = get_prefs()
    scene_props.tile_type = prefs.default_tile_type

bpy.app.handlers.depsgraph_update_pre.append(create_properties_on_activation)
bpy.app.handlers.load_post.append(create_properties_on_load)

bpy.app.handlers.depsgraph_update_post.append(update_mt_scene_props_handler)
bpy.app.handlers.undo_post.append(recreate_properties_on_undo)