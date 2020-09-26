import bpy
from bpy.types import Operator
from ..properties import update_scene_defaults


class MT_OT_Reset_Tile_Defaults(Operator):
    """Reset mt_scene_props of current tile_type."""

    bl_idname = "scene.reset_tile_defaults"
    bl_label = "Reset Defaults"
    bl_options = {'UNDO'}

    def execute(self, context):
        """Execute the operator.

        Args:
            context (bpy.context): Blender context
        """
        update_scene_defaults(self, context)

        return {'FINISHED'}
