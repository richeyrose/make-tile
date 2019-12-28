import os
import bpy
from ..lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. lib.utils.utils import mode


class MT_OT_makeVertGroupsFromFaces(bpy.types.Operator):
    bl_idname = "scene.make_vert_groups_from_faces"
    bl_label = "Make vert groups from faces of cuboid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cuboid_sides_to_vert_groups()
        mode('OBJECT')
        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
