import bpy
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup, Operator
from bpy.props import (
    EnumProperty,
    PointerProperty,
    BoolProperty,
    FloatProperty)
from .scene_props import update_base_defaults, update_main_part_defaults


class MT_OT_Reset_Wall_Defaults(Operator):
    """Reset mt_scene_props and mt_wall_scene_props."""

    bl_idname = "scene.reset_wall_defaults"
    bl_label = "Reset Defaults"
    bl_options = {'UNDO'}

    def execute(self, context):
        """Execute the operator.

        Args:
            context (bpy.context): Blender context
        """
        scene_props = context.scene.mt_scene_props
        wall_scene_props = context.scene.mt_wall_scene_props
        tile_defaults = scene_props['tile_defaults']
        for tile in tile_defaults:
            if tile['type'] in ('STRAIGHT_WALL'):
                defaults = tile['defaults']
                for key, value in defaults.items():
                    setattr(scene_props, key, value)
                    setattr(wall_scene_props, key, value)

        update_main_part_defaults(self, context)
        update_base_defaults(self, context)
        return {'FINISHED'}


class MT_Wall_Properties(PropertyGroup):
    last_selected: PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object)
    wall_position: EnumProperty(
        name="Wall Position",
        items=[
            ("CENTER", "Center", "Wall is in Center of base."),
            ("SIDE", "Side", "Wall is on the side of base.")],
        default="CENTER")
    floor_thickness: FloatProperty(
        name="Floor Thickness",
        default=0.0245,
        step=0.01,
        precision=4)
    is_wall: BoolProperty(
        default=False
    )

@persistent
def update_mt_wall_scene_props_handler(dummy):
    """Check to see if we have a MakeTile wall object selected.

    Updates mt_wall_scene_props based on its mt_wall_tile_props.
    """
    context = bpy.context
    obj = context.object
    wall_scene_props = context.scene.mt_wall_scene_props

    try:
        wall_tile_props = bpy.data.collections[obj.mt_object_props.tile_name].mt_wall_tile_props

        if obj != wall_scene_props.last_selected and wall_tile_props.is_wall:
            for key, value in wall_tile_props.items():
                for k in wall_scene_props.keys():
                    if k == key:
                        wall_scene_props[k] = value
            wall_scene_props.last_selected = obj
    except KeyError:
        pass
    except AttributeError:
        pass

bpy.app.handlers.depsgraph_update_post.append(update_mt_wall_scene_props_handler)

def register():
    bpy.types.Scene.mt_wall_scene_props = PointerProperty(
        type=MT_Wall_Properties)
    bpy.types.Collection.mt_wall_tile_props = PointerProperty(
        type=MT_Wall_Properties)

def unregister():
    del bpy.types.Collection.mt_wall_tile_props
    del bpy.types.Scene.mt_wall_scene_props