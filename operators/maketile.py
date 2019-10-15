import bpy
import os
from .. utils.create import make_cuboid

class MT_OT_makeTile(bpy.types.Operator):
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"

    def execute(self, context):
        