import os
import json
import bpy
from bpy.app.handlers import persistent
from ... utils.registration import get_prefs, get_path
from ... materials.materials import (
    get_blend_filenames,
    load_materials)
from .utils import get_all_subclasses


def load_materials_on_addon_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(load_materials_on_addon_activation)
    prefs = get_prefs()
    default_materials_path = os.path.join(prefs.assets_path, "materials")
    user_materials_path = os.path.join(prefs.user_assets_path, "materials")

    blend_filenames = get_blend_filenames(default_materials_path)
    load_materials(default_materials_path, blend_filenames)

    blend_filenames = get_blend_filenames(user_materials_path)
    load_materials(user_materials_path, blend_filenames)

@persistent
def load_material_libraries(dummy):
    prefs = get_prefs()
    default_materials_path = os.path.join(prefs.assets_path, "materials")
    user_materials_path = os.path.join(prefs.user_assets_path, "materials")

    blend_filenames = get_blend_filenames(default_materials_path)
    load_materials(default_materials_path, blend_filenames)

    blend_filenames = get_blend_filenames(user_materials_path)
    load_materials(user_materials_path, blend_filenames)


def get_tile_type_new(tile_type):
    scene = bpy.context.scene
    scene_props = scene.mt_scene_props
    tile_defaults = scene_props['tile_defaults']

    for default in tile_defaults:
        if default['type'] == tile_type:
            return default['bl_idname']
    return None


@persistent
def update_mt_scene_props_handler(dummy):
    scene_props = bpy.context.scene.mt_scene_props
    if hasattr(bpy.context, 'object'):
        obj = bpy.context.object

        if obj is not None and obj != scene_props.mt_last_selected and obj.mt_object_props.is_mt_object is True and obj in bpy.context.selected_objects:
            obj_props = obj.mt_object_props
            tile_name = obj_props.tile_name
            tile_props = bpy.data.collections[tile_name].mt_tile_props

            scene_props.mt_last_selected = obj

            scene_props.tile_name = tile_props.tile_name
            scene_props.tile_blueprint = tile_props.tile_blueprint
            scene_props.main_part_blueprint = tile_props.main_part_blueprint
            scene_props.tile_type_new = get_tile_type_new(tile_props.tile_type)
            scene_props.base_blueprint = tile_props.base_blueprint

            scene_props.tile_x = tile_props.tile_size[0]
            scene_props.tile_y = tile_props.tile_size[1]
            scene_props.tile_z = tile_props.tile_size[2]

            scene_props.base_x = tile_props.base_size[0]
            scene_props.base_y = tile_props.base_size[1]
            scene_props.base_z = tile_props.base_size[2]

            scene_props.angle = tile_props.angle
            scene_props.leg_1_len = tile_props.leg_1_len
            scene_props.leg_2_len = tile_props.leg_2_len
            scene_props.base_socket_side = tile_props.base_socket_side
            scene_props.base_radius = tile_props.base_radius
            scene_props.wall_radius = tile_props.wall_radius
            scene_props.curve_type = tile_props.curve_type
            scene_props.degrees_of_arc = tile_props.degrees_of_arc

            scene_props.x_native_subdivisions = tile_props.x_native_subdivisions
            scene_props.y_native_subdivisions = tile_props.y_native_subdivisions
            scene_props.z_native_subdivisions = tile_props.z_native_subdivisions
            scene_props.opposite_native_subdivisions = tile_props.opposite_native_subdivisions
            scene_props.curve_native_subdivisions = tile_props.curve_native_subdivisions

            scene_props.leg_1_native_subdivisions = tile_props.leg_1_native_subdivisions
            scene_props.leg_2_native_subdivisions = tile_props.leg_2_native_subdivisions
            scene_props.width_native_subdivisions = tile_props.width_native_subdivisions

            scene_props.openlock_column_type = tile_props.openlock_column_type


def create_properties_on_activation(dummy):
    bpy.app.handlers.depsgraph_update_pre.remove(create_properties_on_activation)
    context = bpy.context
    load_tile_defaults(context)
    refresh_scene_props(context)

@persistent
def create_properties_on_load(dummy):
    context = bpy.context
    load_tile_defaults(context)
    refresh_scene_props(context)

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
    scene_props.tile_type_new = prefs.default_tile_type

bpy.app.handlers.depsgraph_update_pre.append(create_properties_on_activation)
bpy.app.handlers.load_post.append(create_properties_on_load)

bpy.app.handlers.depsgraph_update_post.append(update_mt_scene_props_handler)
bpy.app.handlers.load_post.append(load_material_libraries)
bpy.app.handlers.depsgraph_update_pre.append(load_materials_on_addon_activation)
