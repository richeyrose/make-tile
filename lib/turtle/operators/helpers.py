import bpy
import bmesh
from bpy.props import FloatProperty


class TURTLE_OT_merge(bpy.types.Operator):
    bl_idname = "turtle.merge"
    bl_label = "Merge Verts"
    bl_description = "Merges duplicate vertices. t= threshold"

    t: FloatProperty(default=0.0001)

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.remove_doubles(threshold=self.t)

        return {'FINISHED'}


class TURTLE_OT_bridge(bpy.types.Operator):
    bl_idname = "turtle.bridge"
    bl_label = "Bridge Edge Loops"
    bl_description = "Bridges two edge loops"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.bridge_edge_loops()
        return {'FINISHED'}


class TURTLE_OT_add_vert(bpy.types.Operator):
    bl_idname = "turtle.add_vert"
    bl_label = "Add Vert"
    bl_description = "adds a Vert at the turtle's location"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        mesh = bpy.data.meshes.new("Vert")
        mesh.vertices.add(1)

        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=None)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}
