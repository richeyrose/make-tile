import bpy


class TURTLE_OT_begin_path(bpy.types.Operator):
    bl_idname = "turtle.begin_path"
    bl_label = "Begin path"
    bl_description = "Sets begin_path_vert to index of last vert that has been drawn"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        verts = bpy.context.object.data.vertices
        bpy.context.object['beginpath_active_vert'] = verts.values()[-1].index

        return {'FINISHED'}


class TURTLE_OT_stroke_path(bpy.types.Operator):
    bl_idname = "turtle.stroke_path"
    bl_label = "Stroke path"
    bl_description = "draws an edge between selected vert and vert indexed in beginpath"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        if bpy.context.object.get('beginpath_active_vert') is None:
            return {'PASS_THROUGH'}

        bpy.ops.object.editmode_toggle()

        verts = bpy.context.object.data.vertices

        bpy.context.object.data.vertices[-1].select = True
        bpy.context.object.data.vertices[bpy.context.object['beginpath_active_vert']].select = True

        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.editmode_toggle()

        bpy.context.object.data.vertices[-1].select = True

        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class TURTLE_OT_fill_path(bpy.types.Operator):
    bl_idname = "turtle.fill_path"
    bl_label = "Fill path"
    bl_description = "draws an edge between selected vert and vert indexed in beginpath and then creates a face between all verts created since last beginpath statement"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        if bpy.context.object.get('beginpath_active_vert') is None:
            return {'PASS_THROUGH'}

        bpy.ops.object.editmode_toggle()

        verts = bpy.context.object.data.vertices

        i = bpy.context.object['beginpath_active_vert']

        while i <= verts.values()[-1].index:
            bpy.context.object.data.vertices[i].select = True
            i += 1

        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.edge_face_add()

        bpy.ops.mesh.select_all(action='DESELECT')

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        bpy.context.object.data.vertices[-1].select = True

        return {'FINISHED'}
