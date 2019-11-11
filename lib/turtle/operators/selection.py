import bpy
from bpy.props import StringProperty, FloatProperty, FloatVectorProperty, IntProperty, EnumProperty, BoolProperty
import bmesh
from mathutils import Vector
from .. Utils.utils import select_by_loc, select, activate
from bpy.types import Operator


class TURTLE_OT_select_path(bpy.types.Operator):
    bl_idname = "turtle.select_path"
    bl_label = "Select Path"
    bl_description = "Selects all verts drawn since last Begin Path command"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()

        verts = bpy.context.object.data.vertices

        i = bpy.context.object['beginpath_active_vert']
        while i <= verts.values()[-1].index:
            bpy.context.object.data.vertices[i].select = True
            i += 1

        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class TURTLE_OT_select_all(bpy.types.Operator):
    bl_idname = "turtle.select_all"
    bl_label = "Select All"
    bl_description = "Selects All Vertices"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.mesh.select_all(action='SELECT')

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class TURTLE_OT_select_by_location(bpy.types.Operator):
    bl_idname = "turtle.select_by_location"
    bl_label = "Select By Location"
    bl_description = "Selects all vertices within a bounding cuboid defined by lbound=(0, 0, 0) and ubound=(0, 0, 0)"

    lbound: FloatVectorProperty()
    ubound: FloatVectorProperty()
    select_mode: StringProperty(default='VERT')
    buffer: FloatProperty(default=0.1)
    additive: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        select_by_loc(lbound=self.lbound, ubound=self.ubound, select_mode=self.select_mode, buffer=self.buffer, additive=self.additive)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class TURTLE_OT_select_at_cursor(bpy.types.Operator):
    bl_idname = "turtle.select_at_cursor"
    bl_label = "Select at Cursor"
    bl_description = "Selects vertices at cursor"

    select_mode: StringProperty(default='VERT')
    additive: BoolProperty(default=True)
    buffer: FloatProperty(default=0.1)

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        select_by_loc(lbound=turtle.location, ubound=turtle.location, select_mode=self.select_mode, buffer=self.buffer, additive=self.additive)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class TURTLE_OT_deselect_all(bpy.types.Operator):
    bl_idname = "turtle.deselect_all"
    bl_label = "Select All"
    bl_description = "Selects All Vertices"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}
