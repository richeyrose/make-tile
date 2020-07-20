import os
import bpy
from bpy.app.handlers import persistent
from ... utils.registration import get_prefs
from ... materials.materials import (
    get_blend_filenames,
    load_materials)


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

            scene_props.mt_tile_name = tile_props.tile_name
            scene_props.mt_tile_blueprint = tile_props.tile_blueprint
            scene_props.mt_main_part_blueprint = tile_props.main_part_blueprint
            scene_props.mt_tile_type = tile_props.tile_type
            scene_props.mt_base_blueprint = tile_props.base_blueprint

            scene_props.mt_tile_x = tile_props.tile_size[0]
            scene_props.mt_tile_y = tile_props.tile_size[1]
            scene_props.mt_tile_z = tile_props.tile_size[2]

            scene_props.mt_base_x = tile_props.base_size[0]
            scene_props.mt_base_y = tile_props.base_size[1]
            scene_props.mt_base_z = tile_props.base_size[2]

            scene_props.mt_angle = tile_props.angle
            scene_props.mt_leg_1_len = tile_props.leg_1_len
            scene_props.mt_leg_2_len = tile_props.leg_2_len
            scene_props.mt_base_socket_side = tile_props.base_socket_side
            scene_props.mt_base_radius = tile_props.base_radius
            scene_props.mt_wall_radius = tile_props.wall_radius
            scene_props.mt_curve_type = tile_props.curve_type
            scene_props.mt_degrees_of_arc = tile_props.degrees_of_arc

            scene_props.mt_x_native_subdivisions = tile_props.x_native_subdivisions
            scene_props.mt_y_native_subdivisions = tile_props.y_native_subdivisions
            scene_props.mt_z_native_subdivisions = tile_props.z_native_subdivisions
            scene_props.mt_opposite_native_subdivisions = tile_props.opposite_native_subdivisions
            scene_props.mt_curve_native_subdivisions = tile_props.curve_native_subdivisions

            scene_props.mt_leg_1_native_subdivisions = tile_props.leg_1_native_subdivisions
            scene_props.mt_leg_2_native_subdivisions = tile_props.leg_2_native_subdivisions
            scene_props.mt_width_native_subdivisions = tile_props.width_native_subdivisions

            scene_props.mt_openlock_column_type = tile_props.openlock_column_type

bpy.app.handlers.depsgraph_update_post.append(update_mt_scene_props_handler)
bpy.app.handlers.load_post.append(load_material_libraries)
bpy.app.handlers.depsgraph_update_pre.append(load_materials_on_addon_activation)
