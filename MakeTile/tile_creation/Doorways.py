import bpy
from bpy.types import Operator


class MT_OT_Make_Straight_Doorway(Operator):
    """Create a Straight Doorway."""

    bl_idname = "object.make_straight_doorway"
    bl_label = "Straight Doorway"
    bl_options = {'UNDO'}
    mt_type = "STRAIGHT_DOORWAY"
