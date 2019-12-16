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
        obj = bpy.context.active_object
        if obj is not None:
            return bpy.context.object.mode == 'OBJECT'

    def execute(self, context):
        # object to be trimmed
        obj = context.active_object

        # get collection name / name of tile
        tile_name = obj.users_collection[0].name

        # get tile empty with properties stored on it
        if tile_name + '.empty' in bpy.data.objects:
            tile_empty = bpy.data.objects[tile_name + '.empty']
            trimmers = tile_empty['tile_properties']['trimmers']

            if context.scene.mt_trim_x_neg is True:
                trimmer = trimmers['x_neg']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)
            if context.scene.mt_trim_x_pos is True:
                trimmer = trimmers['x_pos']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)
            if context.scene.mt_trim_y_neg is True:
                trimmer = trimmers['y_neg']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)
            if context.scene.mt_trim_y_pos is True:
                trimmer = trimmers['y_pos']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)
            if context.scene.mt_trim_z_neg is True:
                trimmer = trimmers['z_neg']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)
            if context.scene.mt_trim_z_pos is True:
                trimmer = trimmers['z_pos']
                trim_side(obj, trimmer, context.scene.mt_trim_buffer)

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


def trim_side(obj, trimmer, buffer):
    boolean = obj.modifiers.new(trimmer.name + '_trimmer', 'BOOLEAN')
    boolean.operation = 'DIFFERENCE'
    boolean.object = trimmer
    trimmer.parent = obj
    trimmer.display_type = 'BOUNDS'
    trimmer.hide_viewport = True


def create_x_neg_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]

    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.ri(d=buffer)
    t.dn(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    t.lf(d=0.5)
    mode('OBJECT')
    return bpy.context.object


def create_x_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_right = bound_box[4]

    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_right)))
    t.lf(d=buffer)
    t.dn(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    t.select_all()
    t.ri(d=0.5)
    mode('OBJECT')
    return bpy.context.object


def create_y_neg_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.fd(d=buffer)
    t.lf(d=0.5)
    t.dn(d=0.5)
    t.pd()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.bk(d=0.5)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    mode('OBJECT')
    return bpy.context.object


def create_y_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.fd(d=dimensions[1])
    t.bk(d=buffer)
    t.lf(d=0.5)
    t.dn(d=0.5)
    t.pd()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.fd(d=0.5)
    t.select_all()
    t.up(d=dimensions[2] + 1)
    mode('OBJECT')
    return bpy.context.object


def create_z_pos_trimmer(bound_box, dimensions, buffer):
    deselect_all()

    front_top_left = bound_box[2]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_top_left)))
    t.dn(d=buffer)
    t.lf(d=0.5)
    t.bk(d=1)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.up(d=0.5)
    mode('OBJECT')
    return bpy.context.object


def create_z_neg_trimmer(bound_box, dimensions, buffer):

    deselect_all()

    front_bottom_left = bound_box[0]
    t = bpy.ops.turtle

    t.add_turtle()
    t.pu()
    t.set_position(v=Vector((front_bottom_left)))
    t.up(d=buffer)
    t.lf(d=0.5)
    t.bk(d=0.5)
    t.pd()
    t.fd(d=dimensions[1] + 1)
    t.select_all()
    t.ri(d=dimensions[0] + 1)
    t.select_all()
    t.dn(d=0.5)
    mode('OBJECT')
    return bpy.context.object
