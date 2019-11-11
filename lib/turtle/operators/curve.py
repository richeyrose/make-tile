import bpy
from bpy.props import FloatVectorProperty
from bpy.types import Operator
from mathutils import Vector
from .. Utils.utils import select_by_loc


class TURTLE_OT_quadratic_curve(bpy.types.Operator):
    bl_idname = "turtle.quadratic_curve"
    bl_label = "Quadratic curve"
    bl_description = "moves the turtle on a path described by a quadratic Bezier curve. \
 Keyword Arguments: cp = coordinates of control point, ep = end point"

    cp: FloatVectorProperty()
    ep: FloatVectorProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if bpy.context.object['pendownp']:
            world = bpy.context.object
            world_name = world.name
            bpy.ops.curve.primitive_bezier_curve_add(
                radius=1,
                enter_editmode=True)

            bpy.ops.curve.select_all(action='DESELECT')

            # set location of first spline point and control point
            bpy.context.active_object.data.splines[0].bezier_points[0].co = (0, 0, 0)
            bpy.context.active_object.data.splines[0].bezier_points[0].handle_right = self.cp

            # set location of second control point.
            bpy.context.active_object.data.splines[0].bezier_points[1].co = self.ep
            bpy.context.active_object.data.splines[0].bezier_points[1].handle_right = self.ep

            # set turtle location
            turtle.location = turtle.location + Vector(self.ep)

            # set turtle rotation
            direction_vec = Vector(self.ep) - Vector(self.cp)
            rot_quat = direction_vec.to_track_quat('Y', 'Z')
            turtle.rotation_mode = 'QUATERNION'
            turtle.rotation_quaternion = rot_quat
            turtle.rotation_mode = 'XYZ'

            bpy.ops.object.editmode_toggle()

            # convert curve to mesh and join to turtle_world object
            bpy.ops.object.convert(target='MESH')
            bpy.data.objects[world.name].select_set(True)
            bpy.ops.object.join()
            bpy.context.object.name = world_name

            # merge vertices
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()

            bpy.ops.mesh.select_all(action='DESELECT')

            # select last vert of converted curve
            lbound = turtle.location
            ubound = turtle.location
            select_by_loc(
                lbound,
                ubound,
                select_mode='VERT',
                coords='GLOBAL',
                buffer=0.001)
        else:
            # set turtle location without drawing anything
            turtle.location = self.ep

            # set turtle rotation
            direction_vec = Vector(self.ep) - Vector(self.cp)
            rot_quat = direction_vec.to_track_quat('Y', 'Z')
            turtle.rotation_mode = 'QUATERNION'
            turtle.rotation_quaternion = rot_quat
            turtle.rotation_mode = 'XYZ'

        return {'FINISHED'}


class TURTLE_OT_cubic_curve(bpy.types.Operator):
    bl_idname = "turtle.cubic_curve"
    bl_label = "Cubic curve"
    bl_description = "moves the turtle on a path described by a cubic Bezier curve.\
Keyword Arguments: cp1 / cp2 = coordinates of control points, ep = end point"

    cp1: FloatVectorProperty()
    cp2: FloatVectorProperty()
    ep: FloatVectorProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        turtle = bpy.context.scene.cursor

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if bpy.context.object['pendownp']:
            canvas = bpy.context.object
            canvas_name = canvas.name
            bpy.ops.curve.primitive_bezier_curve_add(
                radius=1,
                enter_editmode=True)
            bpy.ops.curve.select_all(action='DESELECT')
            p0 = bpy.context.active_object.data.splines[0].bezier_points[0]
            p1 = bpy.context.active_object.data.splines[0].bezier_points[1]

            # set location of first spline point and control point
            p0.co = (0, 0, 0)
            bpy.ops.curve.select_all(action='DESELECT')
            p0.select_right_handle = True
            p0.handle_right = self.cp1

            # set location of second spline point and control point
            p1.co = self.ep
            bpy.ops.curve.select_all(action='DESELECT')
            p1.select_left_handle = True
            p1.handle_left = self.cp2

            # set turtle location
            turtle.location = turtle.location + Vector(self.ep)

            # set turtle rotation
            direction_vec = Vector(self.ep) - Vector(self.cp2)
            rot_quat = direction_vec.to_track_quat('Y', 'Z')
            turtle.rotation_mode = 'QUATERNION'
            turtle.rotation_quaternion = rot_quat
            turtle.rotation_mode = 'XYZ'

            bpy.ops.object.editmode_toggle()

            # convert curve to mesh and join to canvas
            bpy.ops.object.convert(target='MESH')
            bpy.data.objects[canvas.name].select_set(True)
            bpy.ops.object.join()
            bpy.context.object.name = canvas_name

            # merge vertices
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()

            bpy.ops.mesh.select_all(action='DESELECT')

            # select last vert of converted curve
            lbound = turtle.location
            ubound = turtle.location
            select_by_loc(
                lbound,
                ubound,
                select_mode='VERT',
                coords='GLOBAL',
                buffer=0.001)
        else:
            # set turtle location without drawing anything
            turtle.location = self.ep

            # set turtle rotation
            direction_vec = Vector(self.ep) - Vector(self.cp2)
            rot_quat = direction_vec.to_track_quat('Y', 'Z')
            turtle.rotation_mode = 'QUATERNION'
            turtle.rotation_quaternion = rot_quat
            turtle.rotation_mode = 'XYZ'

        return {'FINISHED'}
