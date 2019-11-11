import bpy


class TURTLE_OT_merge(bpy.types.Operator):
    bl_idname = "turtle.merge"
    bl_label = "Merge Verts"
    bl_description = "Merges duplicate vertices"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.remove_doubles()

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

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.primitive_vert_add()

        return {'FINISHED'}
