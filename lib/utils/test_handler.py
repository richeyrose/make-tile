import bpy
from bpy.app.handlers import persistent

#TODO: Complete handler and also create a reset to default operator
@persistent
def test_handler(dummy):
    scene = bpy.context.scene
    obj = bpy.context.object

    if obj is not None and obj.mt_object_props.is_mt_object is True and obj in bpy.context.selected_objects:
        tile_props = obj.mt_object_props
        tile_name = tile_props.tile_name
        tile_props = bpy.data.collections[tile_name].mt_tile_props

        scene.mt_tile_x = tile_props.tile_size[0]
        scene.mt_tile_y = tile_props.tile_size[1]
        scene.mt_tile_z = tile_props.tile_size[2]

        print("Is MT object")


bpy.app.handlers.depsgraph_update_post.append(test_handler)