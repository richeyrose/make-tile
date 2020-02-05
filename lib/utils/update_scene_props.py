import bpy
from bpy.app.handlers import persistent


@persistent
def update_mt_scene_props_handler(dummy):
    scene = bpy.context.scene
    obj = bpy.context.object

    if obj is not None and obj != scene.mt_scene_props.mt_last_selected and obj.mt_object_props.is_mt_object is True and obj in bpy.context.selected_objects:
        scene.mt_scene_props.mt_last_selected = obj
        tile_props = obj.mt_object_props
        tile_name = tile_props.tile_name
        tile_props = bpy.data.collections[tile_name].mt_tile_props

        scene.mt_scene_props.mt_tile_name = tile_props.tile_name
        scene.mt_scene_props.mt_tile_units = tile_props.tile_units
        scene.mt_scene_props.mt_tile_blueprint = tile_props.tile_blueprint
        scene.mt_scene_props.mt_main_part_blueprint = tile_props.main_part_blueprint
        scene.mt_scene_props.mt_tile_type = tile_props.tile_type
        scene.mt_scene_props.mt_base_blueprint = tile_props.base_blueprint
        scene.mt_scene_props.mt_displacement_strength = tile_props.displacement_strength
        scene.mt_scene_props.mt_tile_resolution = tile_props.tile_resolution
        scene.mt_scene_props.mt_subdivisions = tile_props.subdivisions

        scene.mt_scene_props.mt_tile_x = tile_props.tile_size[0]
        scene.mt_scene_props.mt_tile_y = tile_props.tile_size[1]
        scene.mt_scene_props.mt_tile_z = tile_props.tile_size[2]

        scene.mt_scene_props.mt_base_x = tile_props.base_size[0]
        scene.mt_scene_props.mt_base_y = tile_props.base_size[1]
        scene.mt_scene_props.mt_base_z = tile_props.base_size[2]

        scene.mt_scene_props.mt_angle = tile_props.angle
        scene.mt_scene_props.mt_leg_1_len = tile_props.leg_1_len
        scene.mt_scene_props.mt_leg_2_len = tile_props.leg_2_len
        scene.mt_scene_props.mt_base_socket_side = tile_props.base_socket_side
        scene.mt_scene_props.mt_base_radius = tile_props.base_radius
        scene.mt_scene_props.mt_wall_radius = tile_props.wall_radius
        scene.mt_scene_props.mt_curve_type = tile_props.curve_type
        scene.mt_scene_props.mt_degrees_of_arc = tile_props.degrees_of_arc
        scene.mt_scene_props.mt_segments = tile_props.segments


bpy.app.handlers.depsgraph_update_post.append(update_mt_scene_props_handler)
