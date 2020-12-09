import textwrap
import addon_utils
from math import radians
import bpy
from bpy.types import Panel, Operator


class MT_PT_Decimator_Panel(Panel):
    bl_order = 10
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Decimator_Panel"
    bl_label = "Decimation Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        layout.operator('scene.mt_decimate_objects', text='Decimate Selected Objects')
        layout.prop(scene_props, 'decimation_merge')
        layout.prop(scene_props, 'decimation_ratio')
        layout.prop(scene_props, 'planar_decimation')
        layout.prop(scene_props, 'planar_decimation_angle')


class MT_OT_Object_Decimator(Operator):
    """Applies all modifiers to the selected objects and, optionally merges them and then decimates them."""
    bl_idname = "scene.mt_decimate_objects"
    bl_label = "Decimate Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT'

    def execute(self, context):
        scene_props = context.scene.mt_scene_props
        merge = scene_props.decimation_merge
        selected_objects = [obj for obj in context.selected_editable_objects if obj.type == 'MESH']

        for obj in selected_objects:
            decimate(context, obj)

        ctx = {
            'selected_objects': selected_objects,
            'selected_editable_objects': selected_objects,
            'object': context.active_object,
            'active_object': context.active_object
        }

        if merge is True:
            bpy.ops.object.join(ctx)

        return {'FINISHED'}


def decimate(context, obj):
    """Decimate the passed in object using the setting in mt_scene_props.

    Args:
        obj (bpy.types.Object): object
    """
    props = context.scene.mt_scene_props

    if props.decimation_ratio < 1:
        mod = obj.modifiers.new('Decimation 1', 'DECIMATE')
        mod.ratio = props.decimation_ratio
    if props.planar_decimation:
        mod = obj.modifiers.new('Decimation 2', 'DECIMATE')
        mod.decimate_type = 'DISSOLVE'
        mod.angle_limit = radians(props.planar_decimation_angle)

    depsgraph = context.evaluated_depsgraph_get()
    object_eval = obj.evaluated_get(depsgraph)
    object_eval = obj.evaluated_get(depsgraph)
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
    obj.modifiers.clear()
    obj.data = mesh_from_eval
