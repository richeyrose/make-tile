import bpy
import os
from .. utils.create import cuboid_faces_to_vert_groups

class MT_OT_makeVertGroupsFromFaces(bpy.types.Operator):
    bl_idname = "scene.make_vert_groups_from_faces"
    bl_label = "Make vert groups from faces of cuboid"

    def execute(self, context):
        cuboid_faces_to_vert_groups()
        return {'FINISHED'}
    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)