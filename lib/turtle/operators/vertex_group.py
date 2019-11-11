import bpy
from bpy.props import StringProperty


class TURTLE_OT_new_vert_group(bpy.types.Operator):
    bl_idname = "turtle.new_vert_group"
    bl_label = "New Vertex Group"
    bl_description = "Creates new vertex group"

    name: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.context.object.vertex_groups.new(name=self.name)

        return {'FINISHED'}


class TURTLE_OT_select_vert_group(bpy.types.Operator):
    bl_idname = "turtle.select_vert_group"
    bl_label = "Select Vertex Group"
    bl_description = "Selects all verts in vertex group. vg = Vertex group name"

    vg: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.vertex_group_set_active(group=self.vg)
        bpy.ops.object.vertex_group_select()

        return {'FINISHED'}


class TURTLE_OT_deselect_vert_group(bpy.types.Operator):
    bl_idname = "turtle.deselect_vert_group"
    bl_label = "Deselect Vertex Group"
    bl_description = "Deselects all verts in vertex group. vg = Vertex group name"

    vg: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.vertex_group_set_active(group=self.vg)
        bpy.ops.object.vertex_group_deselect()

        return {'FINISHED'}


class TURTLE_OT_add_to_vert_group(bpy.types.Operator):
    bl_idname = "turtle.add_to_vert_group"
    bl_label = "Add to Vertex Group"
    bl_description = "Adds selected verts to vertex group. vg = Vertex group name"

    vg: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.vertex_group_set_active(group=self.vg)
        bpy.ops.object.vertex_group_assign()

        return {'FINISHED'}


class TURTLE_OT_remove_from_vert_group(bpy.types.Operator):
    bl_idname = "turtle.remove_from_vert_group"
    bl_label = "Remove from Vertex Group"
    bl_description = "Removes selected verts from vertex group. vg = Vertex group name"

    vg: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.ops.object.vertex_group_set_active(group=self.vg)
        bpy.ops.object.vertex_group_remove_from()

        return {'FINISHED'}
