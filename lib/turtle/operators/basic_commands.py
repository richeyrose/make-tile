from math import degrees, radians, pi
import bpy
from bpy.props import StringProperty, FloatProperty, FloatVectorProperty, IntProperty, EnumProperty, BoolProperty
import bmesh
from mathutils import Vector
from ...utils.selection import select_by_loc, select, activate
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper


# Turtle world commands
class TURTLE_OT_add_turtle(Operator, AddObjectHelper):
    """Adds an empty turtle world"""
    bl_idname = "turtle.add_turtle"
    bl_label = "Turtle"
    bl_description = "Adds an empty turtle world"
    bl_options = {'REGISTER', 'UNDO'}

    # generic transform props
    align_items = (
        ('WORLD', "World", "Align the new object to the world"),
        ('VIEW', "View", "Align the new object to the view"),
        ('CURSOR', "3D Cursor", "Use the 3D cursor orientation for the new object")
    )
    align: EnumProperty(
        name="Align",
        items=align_items,
        default='WORLD',
        update=AddObjectHelper.align_update_callback)

    location: FloatVectorProperty(
        name="Location",
        subtype='TRANSLATION',
    )
    rotation: FloatVectorProperty(
        name="Rotation",
        subtype='EULER',
    )

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):

        obj = bpy.context.active_object

        # create new empty turtle world
        world_mesh = bpy.data.meshes.new("world_mesh")
        new_world = bpy.data.objects.new("turtle_world", world_mesh)

        # link object to active collection
        bpy.context.layer_collection.collection.objects.link(new_world)

        # we will use the scene cursor as our turtle
        turtle = bpy.context.scene.cursor

        # zero the turtle rotation relative to turtle world
        turtle.rotation_euler = self.rotation

        select(new_world.name)
        activate(new_world.name)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        bpy.ops.object.mode_set(mode='EDIT')
        context.tool_settings.mesh_select_mode = (True, False, False)

        # create two object properties
        # pen state
        new_world['pendownp'] = True

        # index of active vert when beginpath is called
        new_world['beginpath_active_vert'] = 0

        return {'FINISHED'}

    # TODO: find suitable icon or make one
    def add_object_button(self, _context):
        """"Adds an add turtle option to the add mesh menu"""
        self.layout.operator(
            TURTLE_OT_add_turtle.bl_idname,
            text="Add Turtle",
            icon='PLUGIN')

    # TODO: put in link to docs
    def add_object_manual_map(self):
        """ This allows you to right click on a button and link to documentation"""
        url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
        url_manual_mapping = (
            ("bpy.ops.mesh.add_object", "scene_layout/object/types.html"),
        )
        return url_manual_prefix, url_manual_mapping


class TURTLE_OT_clear_screen(bpy.types.Operator):
    bl_idname = "turtle.clear_screen"
    bl_label = "Clear Turtle World"
    bl_description = "Deletes mesh in turtle world and homes turtle."

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        bpy.ops.turtle.home()
        bpy.ops.turtle.clean()

        return {'FINISHED'}


class TURTLE_OT_home(bpy.types.Operator):
    bl_idname = "turtle.home"
    bl_label = "Home Turtle"
    bl_description = "Set turtle location and rotation to object origin"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        context.scene.cursor.location = context.object.location
        context.scene.cursor.rotation_euler = context.object.rotation_euler

        return {'FINISHED'}


class TURTLE_OT_clean(bpy.types.Operator):
    bl_idname = "turtle.clean"
    bl_label = "Clean"
    bl_description = "deletes mesh, leaves turtle where it is"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete()
        context.object['beginpath_active_vert'] = 0

        if bpy.context.object['pendownp']:
            bpy.ops.turtle.add_vert()

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


# Pen commands
class TURTLE_OT_pen_down(bpy.types.Operator):
    bl_idname = "turtle.pen_down"
    bl_label = "Pen Down"
    bl_description = "Lowers the pen so that the turtle will draw on move"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.context.object['pendownp'] = True

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


class TURTLE_OT_pen_up(bpy.types.Operator):
    bl_idname = "turtle.pen_up"
    bl_label = "Pen Up"
    bl_description = "Raises the pen so that the turtle will NOT draw on move"

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.context.object['pendownp'] = False

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return {'FINISHED'}


# Basic movement commands
class TURTLE_OT_forward(bpy.types.Operator):
    bl_idname = "turtle.forward"
    bl_label = "Move Forward"
    bl_description = "Moves the turtle forward. d = distance in blender units, m = move mode"

    d: FloatProperty()
    m: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        # make sure selection is properly updated
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        """ check our object has a "pendownp" property that
         describes the pen state and if not add one"""
        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        # check if pen is down
        if context.object['pendownp']:
            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()

            # extrude vert along cursor Y
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, self.d, 0),
                        "orient_type": 'CURSOR'})
            # or move vert along cursor Y if in move mode
            else:
                bpy.ops.transform.translate(
                    value=(0, self.d, 0),
                    orient_type='CURSOR')

        # move turtle forward
        bpy.ops.transform.translate(
            value=(0, self.d, 0),
            orient_type='CURSOR',
            cursor_transform=True)

        return {'FINISHED'}


class TURTLE_OT_backward(bpy.types.Operator):
    bl_idname = "turtle.backward"
    bl_label = "Move Backward"
    bl_description = "Moves the turtle Backward. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if context.object['pendownp']:
            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, -self.d, 0),
                        "orient_type": 'CURSOR'})
            else:
                bpy.ops.transform.translate(
                    value=(0, -self.d, 0),
                    orient_type='CURSOR')

        bpy.ops.transform.translate(
            value=(0, -self.d, 0),
            orient_type='CURSOR',
            cursor_transform=True)

        return {'FINISHED'}


class TURTLE_OT_up(bpy.types.Operator):
    bl_idname = "turtle.up"
    bl_label = "Move Up"
    bl_description = "Moves the turtle Up. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if context.object['pendownp']:
            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, 0, self.d),
                        "orient_type": 'CURSOR'})
            else:
                bpy.ops.transform.translate(
                    value=(0, 0, self.d),
                    orient_type='CURSOR')

        bpy.ops.transform.translate(
            value=(0, 0, self.d),
            orient_type='CURSOR',
            cursor_transform=True)

        return {'FINISHED'}


class TURTLE_OT_down(bpy.types.Operator):
    bl_idname = "turtle.down"
    bl_label = "Move Down"
    bl_description = "Moves the turtle down. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if context.object['pendownp']:

            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, 0, -self.d),
                        "orient_type": 'CURSOR'})
            else:
                bpy.ops.transform.translate(
                    value=(0, 0, -self.d),
                    orient_type='CURSOR')

        bpy.ops.transform.translate(
            value=(0, 0, -self.d),
            orient_type='CURSOR',
            cursor_transform=True)

        return {'FINISHED'}


class TURTLE_OT_left(bpy.types.Operator):
    bl_idname = "turtle.left"
    bl_label = "Move Left"
    bl_description = "Moves the turtle left. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if context.object['pendownp']:
            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (-self.d, 0, 0),
                        "orient_type": 'CURSOR'})
            else:
                bpy.ops.transform.translate(
                    value=(-self.d, 0, 0),
                    orient_type='CURSOR')

        bpy.ops.transform.translate(
            value=(-self.d, 0, 0),
            orient_type='CURSOR',
            cursor_transform=True)
        return {'FINISHED'}


class TURTLE_OT_right(bpy.types.Operator):
    bl_idname = "turtle.right"
    bl_label = "Move Right"
    bl_description = "Moves the turtle right. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty(default=False)
    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        if bpy.context.object.get('pendownp') is None:
            # pen state
            bpy.context.object['pendownp'] = True

        if context.object['pendownp']:
            if len(bpy.context.object.data.vertices) == 0:
                bpy.ops.turtle.add_vert()
            if not self.m:
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (self.d, 0, 0),
                        "orient_type": 'CURSOR'})
            else:
                bpy.ops.transform.translate(
                    value=(self.d, 0, 0),
                    orient_type='CURSOR')

        bpy.ops.transform.translate(
            value=(self.d, 0, 0),
            orient_type='CURSOR',
            cursor_transform=True)
        return {'FINISHED'}


class TURTLE_OT_arc(bpy.types.Operator):
    bl_idname = "turtle.arc"
    bl_label = "Draw Arc"
    bl_description = "Draws an arc with the Turtle at its center, leaving the turtle in place. \
        r = radius, d = degrees of arc, s = segments in arc"

    r: FloatProperty()
    d: FloatProperty()
    s: IntProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        circumference = 2 * pi * self.r
        segment_length = circumference / ((360 / self.d) * self.s)
        rotation_amount = self.d / self.s

        turtle = bpy.context.scene.cursor
        t = bpy.ops.turtle
        start_loc = turtle.location.copy()
        start_rot = turtle.rotation_euler.copy()
        t.deselect_all()
        t.pu()
        t.fd(d=self.r)
        t.add_vert()
        t.pd()
        t.rt(d=90)
        t.rt(d=rotation_amount / 2)

        for i in range(self.s):
            t.fd(d=segment_length)
            t.rt(d=rotation_amount)

        t.pu()
        turtle.location = start_loc
        turtle.rotation_euler = start_rot
        return {'FINISHED'}


class TURTLE_OT_left_turn(bpy.types.Operator):
    bl_idname = "turtle.left_turn"
    bl_label = "Rotate left"
    bl_description = "Rotate the turtle left. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0],
            turtle.rotation_euler[1],
            turtle.rotation_euler[2] + radians(self.d)]
        return {'FINISHED'}


class TURTLE_OT_right_turn(bpy.types.Operator):
    bl_idname = "turtle.right_turn"
    bl_label = "Rotate reight"
    bl_description = "Rotate the turtle right. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0],
            turtle.rotation_euler[1],
            turtle.rotation_euler[2] - radians(self.d)]
        return {'FINISHED'}


class TURTLE_OT_look_up(bpy.types.Operator):
    bl_idname = "turtle.look_up"
    bl_label = "Turtle look up"
    bl_description = "Pitch turtle up (look up). d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0] + radians(self.d),
            turtle.rotation_euler[1],
            turtle.rotation_euler[2]]
        return {'FINISHED'}


class TURTLE_OT_look_down(bpy.types.Operator):
    bl_idname = "turtle.look_down"
    bl_label = "Turtle look down"
    bl_description = "Pitch turtle down (look down). d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0] - radians(self.d),
            turtle.rotation_euler[1],
            turtle.rotation_euler[2]]
        return {'FINISHED'}


class TURTLE_OT_roll_left(bpy.types.Operator):
    bl_idname = "turtle.roll_left"
    bl_label = "Turtle roll left"
    bl_description = "Roll turtle around Y axis. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0],
            turtle.rotation_euler[1] - radians(self.d),
            turtle.rotation_euler[2]]
        return {'FINISHED'}


class TURTLE_OT_roll_right(bpy.types.Operator):
    bl_idname = "turtle.roll_right"
    bl_label = "Turtle roll right"
    bl_description = "Roll turtle around Y axis. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor
        turtle.rotation_euler = [
            turtle.rotation_euler[0],
            turtle.rotation_euler[1] + radians(self.d),
            turtle.rotation_euler[2]]
        return {'FINISHED'}


class TURTLE_OT_set_pos(bpy.types.Operator):
    bl_idname = "turtle.set_position"
    bl_label = "Set turtle posiiton"
    bl_description = "moves the turtle to the specified location. v = location"

    v: FloatVectorProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):

        bpy.context.scene.cursor.location = (self.v)
        return {'FINISHED'}


class TURTLE_OT_set_rotation(bpy.types.Operator):
    bl_idname = "turtle.set_rotation"
    bl_label = "Set turtle rotation"
    bl_description = "Set the turtles rotation. v = rotation in degrees (0, 0, 0)"

    v: FloatVectorProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        turtle.rotation_euler = [
            radians(self.v[0]),
            radians(self.v[1]),
            radians(self.v[2])]
        return {'FINISHED'}


class TURTLE_OT_set_heading(bpy.types.Operator):
    bl_idname = "turtle.set_heading"
    bl_label = "Set turtle heading"
    bl_description = "Rotate the turtle to face the specified horizontal heading. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        turtle.rotation_euler = [
            turtle.rotation_euler[0],
            turtle.rotation_euler[1],
            radians(self.d)]
        return {'FINISHED'}


class TURTLE_OT_set_pitch(bpy.types.Operator):
    bl_idname = "turtle.set_pitch"
    bl_label = "Set turtle pitch"
    bl_description = "Rotate the turtle to face the specified pitch on the X axis. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        turtle.rotation_euler = [
            radians(self.d),
            turtle.rotation_euler[1],
            turtle.rotation_euler[2]]
        return {'FINISHED'}


class TURTLE_OT_set_roll(bpy.types.Operator):
    bl_idname = "turtle.set_roll"
    bl_label = "Set turtle roll"
    bl_description = "Rotate the turtle around Y. d = degrees"

    d: FloatProperty()

    @classmethod
    def poll(cls, context):
        return context.object.mode == 'EDIT'

    def execute(self, context):
        turtle = bpy.context.scene.cursor

        turtle.rotation_euler = [
            turtle.rotation_euler[1],
            radians(self.d),
            turtle.rotation_euler[2]]
        return {'FINISHED'}
