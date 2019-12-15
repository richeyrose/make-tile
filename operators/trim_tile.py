import bpy
from .. lib.utils.selection import select, deselect_all, select_all, activate
from .. lib.utils.utils import mode
from mathutils import Vector


class MT_OT_Tile_Trimmer(bpy.types.Operator):
    """Operator class used to trim tiles before export"""
    bl_idname = "scene.trim_tile"
    bl_label = "Trim Tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None and bpy.context.active_object is not None:
            return bpy.context.object.mode == 'OBJECT'

    def execute(self, context):

        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_trim_buffer = bpy.props.FloatProperty(
            name="Buffer",
            description="Buffer to use for trimming. Helps Booleans work",
            default=0.0001,
            precision=4
        )

        bpy.types.Scene.mt_trim_x_neg = bpy.props.BoolProperty(
            name="X Negative",
            description="Trim the X negative side of tile",
            default=False
        )

        bpy.types.Scene.mt_trim_x_pos = bpy.props.BoolProperty(
            name="X Positive",
            description="Trim the X positive side of tile",
            default=False
        )

        bpy.types.Scene.mt_trim_y_neg = bpy.props.BoolProperty(
            name="Y Negative",
            description="Trim the Y negative side of tile",
            default=False
        )

        bpy.types.Scene.mt_trim_y_pos = bpy.props.BoolProperty(
            name="Y Positive",
            description="Trim the Y positive side of tile",
            default=False
        )

        bpy.types.Scene.mt_trim_z_neg = bpy.props.BoolProperty(
            name="Z Negative",
            description="Trim the Z positive side of tile",
            default=False
        )

        bpy.types.Scene.mt_trim_z_pos = bpy.props.BoolProperty(
            name="Z Positive",
            description="Trim the Z positive side of tile",
            default=False
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_trim_x_neg
        del bpy.types.Scene.mt_trim_x_pos
        del bpy.types.Scene.mt_trim_y_neg
        del bpy.types.Scene.mt_trim_y_pos
        del bpy.types.Scene.mt_trim_z_neg
        del bpy.types.Scene.mt_trim_z_pos


def trim_left(obj, buffer):
    trimmer = create_left_trimmer(obj, buffer)
    boolean = obj.modifiers.new('Left_trimmer', 'BOOLEAN')
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer
    trimmer.parent = obj
    trimmer.display_type = 'BOUNDS'
    trimmer.hide_viewport = True


def trim_right(obj, buffer):
    trimmer = create_right_trimmer(obj, buffer)
    boolean = obj.modifiers.new('Right_trimmer', 'BOOLEAN')
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer
    trimmer.parent = obj
    trimmer.display_type = 'BOUNDS'
    trimmer.hide_viewport = True


def trim_top(obj, buffer):
    trimmer = create_top_trimmer(obj, buffer)
    boolean = obj.modifiers.new('Top_trimmer', 'BOOLEAN')
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer
    trimmer.parent = obj
    trimmer.display_type = 'BOUNDS'
    trimmer.hide_viewport = True


def trim_bottom(obj, buffer):
    trimmer = create_bottom_trimmer(obj, buffer)
    boolean = obj.modifiers.new('Bottom_trimmer', 'BOOLEAN')
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer
    trimmer.parent = obj
    trimmer.display_type = 'BOUNDS'
    trimmer.hide_viewport = True


def create_left_trimmer(obj, buffer):
    deselect_all()
    if obj['original_bound_box'] is not None:
        front_bottom_left = obj['original_bound_box'][0]
    else:
        front_bottom_left = obj.bound_box[0]
    dimensions = obj.dimensions
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.ri(d=buffer)
    t.dn(d=2)
    t.bk(d=2)
    t.pd()
    t.fd(d=dimensions[1] + 4)
    t.select_all()
    t.up(d=dimensions[2] + 4)
    t.select_all()
    t.lf(d=2)
    mode('OBJECT')
    return bpy.context.object


def create_right_trimmer(obj, buffer):
    deselect_all()
    if obj['original_bound_box'] is not None:
        front_bottom_right = obj['original_bound_box'][4]
    else:
        front_bottom_right = obj.bound_box[4]
    dimensions = obj.dimensions
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_right)))
    t.lf(d=buffer)
    t.dn(d=2)
    t.bk(d=2)
    t.pd()
    t.fd(d=dimensions[1] + 4)
    t.select_all()
    t.up(d=dimensions[2] + 4)
    t.select_all()
    t.ri(d=2)
    mode('OBJECT')
    return bpy.context.object


def create_top_trimmer(obj, buffer):
    deselect_all()
    if obj['original_bound_box'] is not None:
        front_top_left = obj['original_bound_box'][2]
    else:
        front_top_left = obj.bound_box[2]
    dimensions = obj.dimensions
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_top_left)))
    t.dn(d=buffer)
    t.lf(d=2)
    t.bk(d=2)
    t.pd()
    t.fd(d=dimensions[1] + 4)
    t.select_all()
    t.ri(d=dimensions[0] + 4)
    t.select_all()
    t.up(d=2)
    mode('OBJECT')
    return bpy.context.object


def create_bottom_trimmer(obj, buffer):
    deselect_all()
    if obj['original_bound_box'] is not None:
        front_bottom_left = obj['original_bound_box'][0]
    else:
        front_bottom_left = obj.bound_box[0]
    dimensions = obj.dimensions
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.up(d=buffer)
    t.lf(d=2)
    t.bk(d=2)
    t.pd()
    t.fd(d=dimensions[1] + 4)
    t.select_all()
    t.ri(d=dimensions[0] + 4)
    t.select_all()
    t.dn(d=2)
    mode('OBJECT')
    return bpy.context.object
