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
    load_material_libraries()
    context = bpy.context
    initialise_scene_props(context)


@persistent
def create_properties_on_load(dummy):
    load_material_libraries()
    context = bpy.context
    initialise_scene_props(context)

def load_material_libraries():
    prefs = get_prefs()
    default_materials_path = os.path.join(prefs.assets_path, "materials")
    user_materials_path = os.path.join(prefs.user_assets_path, "materials")

    blend_filenames = get_blend_filenames(default_materials_path)
    materials = load_materials(default_materials_path, blend_filenames)

    blend_filenames = get_blend_filenames(user_materials_path)
    materials.extend(load_materials(user_materials_path, blend_filenames))


@persistent
def update_mt_scene_props_handler(dummy):
    """Updates mt_scene_props based on mt_tile_props of selected object.

    This means that when the user selects an existing tile they can easily
    create one with the same properties.
    """
    try:
        context = bpy.context
        obj = context.object
        scene_props = context.scene.mt_scene_props
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


def load_tile_defaults(context):
    """Load tile defaults into memory."""
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
            return tile_defaults
    return False


def initialise_scene_props(context):
    prefs = get_prefs()
    scene_props = context.scene.mt_scene_props
    scene_props.tile_type = prefs.default_tile_type
    tile_defaults = load_tile_defaults(context)

    for tile in tile_defaults:
        if tile['type'] == scene_props.tile_type:
            defaults = tile['defaults']
            for key, value in defaults.items():
                setattr(scene_props, key, value)

            base_blueprint = scene_props.base_blueprint
            base_defaults = defaults['base_defaults']
            for key, value in base_defaults.items():
                if key == base_blueprint:
                    for k, v in value.items():
                        setattr(scene_props, k, v)
                    break

            main_part_blueprint = scene_props.main_part_blueprint
            main_part_defaults = defaults['tile_defaults']
            for key, value in main_part_defaults.items():
                if key == main_part_blueprint:
                    for k, v in value.items():
                        setattr(scene_props, k, v)
                    break
            break


bpy.app.handlers.depsgraph_update_pre.append(create_properties_on_activation)
bpy.app.handlers.load_post.append(create_properties_on_load)
bpy.app.handlers.depsgraph_update_post.append(update_mt_scene_props_handler)
