import bpy
from bpy.props import StringProperty, FloatProperty, FloatVectorProperty, IntProperty, BoolProperty


class TURTLE_OT_clear_screen_alias(bpy.types.Operator):
    bl_idname = "turtle.cs"
    bl_label = "Clear Turtle World"
    bl_description = "Deletes mesh in turtle world."

    def execute(self, context):
        bpy.ops.turtle.clear_screen()

        return {'FINISHED'}


class TURTLE_OT_pen_down_alias(bpy.types.Operator):
    bl_idname = "turtle.pd"
    bl_label = "Pend Down"
    bl_description = "Lowers the pen so that the turtle will draw on move"

    def execute(self, context):
        bpy.ops.turtle.pen_down()

        return {'FINISHED'}


class TURTLE_OT_pen_up_alias(bpy.types.Operator):
    bl_idname = "turtle.pu"
    bl_label = "Pen Up"
    bl_description = "Raises the pen so that the turtle will NOT draw on move"

    def execute(self, context):
        bpy.ops.turtle.pen_up()
        return {'FINISHED'}


class TURTLE_OT_forward_alias(bpy.types.Operator):
    bl_idname = "turtle.fd"
    bl_label = "Move Forward"
    bl_description = "Moves the turtle forward. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty()
    
    def execute(self, context):
        bpy.ops.turtle.forward(d=self.d, m=self.m)

        return {'FINISHED'}


class TURTLE_OT_backward_alias(bpy.types.Operator):
    bl_idname = "turtle.bk"
    bl_label = "Move Backward"
    bl_description = "Moves the turtle Backward. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty()

    def execute(self, context):
        bpy.ops.turtle.backward(d=self.d, m=self.m)
        return {'FINISHED'}


class TURTLE_OT_down_alias(bpy.types.Operator):
    bl_idname = "turtle.dn"
    bl_label = "Move Down"
    bl_description = "Moves the turtle down. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty()

    def execute(self, context):
        bpy.ops.turtle.down(d=self.d, m=self.m)
        return {'FINISHED'}


class TURTLE_OT_left_alias(bpy.types.Operator):
    bl_idname = "turtle.lf"
    bl_label = "Move Left"
    bl_description = "Moves the turtle left. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty()

    def execute(self, context):
        bpy.ops.turtle.left(d=self.d, m=self.m)
        return {'FINISHED'}


class TURTLE_OT_right_alias(bpy.types.Operator):
    bl_idname = "turtle.ri"
    bl_label = "Move Right"
    bl_description = "Moves the turtle right. d = distance in blender units"

    d: FloatProperty()
    m: BoolProperty()

    def execute(self, context):
        bpy.ops.turtle.right(d=self.d, m=self.m)
        return {'FINISHED'}


class TURTLE_OT_left_turn_alias(bpy.types.Operator):
    bl_idname = "turtle.lt"
    bl_label = "Rotate left"
    bl_description = "Rotate the turtle left. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.left_turn(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_right_turn_alias(bpy.types.Operator):
    bl_idname = "turtle.rt"
    bl_label = "Rotate reight"
    bl_description = "Rotate the turtle right. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.right_turn(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_look_up_alias(bpy.types.Operator):
    bl_idname = "turtle.lu"
    bl_label = "Turtle look up"
    bl_description = "Pitch turtle up (look up). d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.look_up(d=self.d)

        return {'FINISHED'}


class TURTLE_OT_look_down_alias(bpy.types.Operator):
    bl_idname = "turtle.ld"
    bl_label = "Turtle look down"
    bl_description = "Pitch turtle down (look down). d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.look_down(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_roll_left_alias(bpy.types.Operator):
    bl_idname = "turtle.rl"
    bl_label = "Turtle roll left"
    bl_description = "Roll turtle around Y axis. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.roll_left(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_roll_right_alias(bpy.types.Operator):
    bl_idname = "turtle.rr"
    bl_label = "Turtle roll right"
    bl_description = "Roll turtle around Y axis. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.roll_right(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_set_pos_alias(bpy.types.Operator):
    bl_idname = "turtle.setp"
    bl_label = "Set turtle position"
    bl_description = "moves the turtle to the specified location. v = location"

    v: FloatVectorProperty()

    def execute(self, context):
        bpy.ops.turtle.set_position(v=self.v)
        return {'FINISHED'}


class TURTLE_OT_set_rotation_alias(bpy.types.Operator):
    bl_idname = "turtle.setrot"
    bl_label = "Set turtle rotation"
    bl_description = "Set the turtles rotation. v = rotation in degrees (0, 0, 0)"

    v: FloatVectorProperty()

    def execute(self, context):
        bpy.ops.turtle.set_rotation(v=self.v)
        return {'FINISHED'}


class TURTLE_OT_set_heading_alias(bpy.types.Operator):
    bl_idname = "turtle.seth"
    bl_label = "Set turtle heading"
    bl_description = "Rotate the turtle to face the specified horizontal heading. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.set_heading(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_set_pitch_alias(bpy.types.Operator):
    bl_idname = "turtle.setpi"
    bl_label = "Set turtle pitch"
    bl_description = "Rotate the turtle to face the specified pitch on the X axis. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.set_pitch(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_set_roll_alias(bpy.types.Operator):
    bl_idname = "turtle.setr"
    bl_label = "Set turtle roll"
    bl_description = "Rotate the turtle around Y. d = degrees"

    d: FloatProperty()

    def execute(self, context):
        bpy.ops.turtle.set_roll(d=self.d)
        return {'FINISHED'}


class TURTLE_OT_quadratic_curve_alias(bpy.types.Operator):
    bl_idname = "turtle.qc"
    bl_label = "Quadratic curve"
    bl_description = "moves the turtle on a path described by a quadratic Bezier curve. \
 Keyword Arguments: cp = coordinates of control point, ep = end point"

    cp: FloatVectorProperty()
    ep: FloatVectorProperty()

    def execute(self, context):
        bpy.ops.turtle.quadratic_curve(cp=self.cp, ep=self.ep)
        return {'FINISHED'}


class TURTLE_OT_cubic_curve_alias(bpy.types.Operator):
    bl_idname = "turtle.cc"
    bl_label = "Cubic curve"
    bl_description = "moves the turtle on a path described by a cubic Bezier curve.\
Keyword Arguments: cp1 / cp2 = coordinates of control points, ep = end point"

    cp1: FloatVectorProperty()
    cp2: FloatVectorProperty()
    ep: FloatVectorProperty()

    def execute(self, context):
        bpy.ops.turtle.cubic_curve(cp1=self.cp1, cp2=self.cp2, ep=self.ep)
        return {'FINISHED'}


class TURTLE_OT_select_path_alias(bpy.types.Operator):
    bl_idname = "turtle.selp"
    bl_label = "Select Path"
    bl_description = "Selects all verts drawn since last Begin Path command"

    def execute(self, context):
        bpy.ops.select_path()
        return {'FINISHED'}


class TURTLE_OT_select_all_alias(bpy.types.Operator):
    bl_idname = "turtle.sa"
    bl_label = "Select All"
    bl_description = "Selects All Vertices"

    def execute(self, context):
        bpy.ops.turtle.select_all()
        return {'FINISHED'}


class TURTLE_OT_deselect_all_alias(bpy.types.Operator):
    bl_idname = "turtle.da"
    bl_label = "Select All"
    bl_description = "Selects All Vertices"

    def execute(self, context):
        bpy.ops.turtle.deselect_all()
        return {'FINISHED'}


class TURTLE_OT_new_vert_group_alias(bpy.types.Operator):
    bl_idname = "turtle.nvg"
    bl_label = "New Vertex Group"
    bl_description = "Creates new vertex group"

    def execute(self, context):
        bpy.ops.turtle.new_vert_group()
        return{'FINISHED'}


class TURTLE_OT_select_vert_group_alias(bpy.types.Operator):
    bl_idname = "turtle.svg"
    bl_label = "Select Vertex Group"
    bl_description = "Selects all verts in vertex group. vg = Vertex group name"

    vg: StringProperty()

    def execute(self, context):
        bpy.ops.turtle.select_vert_group(vg=self.vg)
        return {'FINISHED'}


class TURTLE_OT_deselect_vert_group_alias(bpy.types.Operator):
    bl_idname = "turtle.dvg"
    bl_label = "Deselect Vertex Group"
    bl_description = "Deselects all verts in vertex group. vg = Vertex group name"

    vg: StringProperty()

    def execute(self, context):
        bpy.ops.turtle.deselect_vert_group(vg=self.vg)
        return {'FINISHED'}


class TURTLE_OT_add_to_vert_group_alias(bpy.types.Operator):
    bl_idname = "turtle.avg"
    bl_label = "Add to Vertex Group"
    bl_description = "Adds selected verts to vertex group. vg = Vertex group name"

    vg: StringProperty()

    def execute(self, context):
        bpy.ops.turtle.add_to_vert_group(vg=self.vg)
        return{'FINISHED'}


class TURTLE_OT_remove_from_vert_group_alias(bpy.types.Operator):
    bl_idname = "turtle.rvg"
    bl_label = "Remove from Vertex Group"
    bl_description = "Removes selected verts from vertex group. vg = Vertex group name"

    vg: StringProperty()

    def execute(self, context):
        bpy.ops.turtle.remove_from_vertex_group(vg=self.vg)
        return {'FINISHED'}
