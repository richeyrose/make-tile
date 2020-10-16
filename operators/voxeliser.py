import textwrap
import bpy
import addon_utils
from bpy.types import Panel
from .. lib.utils.collections import get_objects_owning_collections
from ..lib.utils.selection import deselect_all, select, activate

class MT_PT_Voxelise_Panel(Panel):
    bl_order = 9
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Make Tile"
    bl_idname = "MT_PT_Voxelise_Panel"
    bl_label = "Voxelise Settings"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.type in {'MESH'}

    def draw(self, context):
        scene = context.scene
        scene_props = scene.mt_scene_props
        layout = self.layout

        char_width = 9  # TODO find a way of actually getting this rather than guessing
        print_tools_txt = "For more options please enable the 3D print Tools addon included with blender"
        
        # get panel width so we can line wrap print_tools_txt
        tool_shelf = None
        area = bpy.context.area

        for region in area.regions:
            if region.type == 'UI':
                tool_shelf = region

        width = tool_shelf.width / char_width
        wrapped = textwrap.wrap(print_tools_txt, width)

        layout.operator('scene.mt_voxelise_objects', text='Voxelise Objects')
        layout.prop(scene_props, 'voxel_size')
        layout.prop(scene_props, 'voxel_adaptivity')
        layout.prop(scene_props, 'voxel_merge')

        if addon_utils.check("object_print3d_utils") == (True, True):
            layout.prop(scene_props, 'fix_non_manifold')
        else:
            for line in wrapped:
                row = layout.row()
                row.label(text=line)


class MT_OT_Object_Voxeliser(bpy.types.Operator):
    """Applies all modifiers to the selected objects and, optionally merges them
    and then voxelises objects"""
    bl_idname = "scene.mt_voxelise_objects"
    bl_label = "Voxelise Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT'

    def execute(self, context):
        scene_props = context.scene.mt_scene_props
        merge = scene_props.voxel_merge
        selected_objects = [obj for obj in context.selected_editable_objects if obj.type == 'MESH']
        meshes = []

        depsgraph = context.evaluated_depsgraph_get()

        for obj in selected_objects:
            if context.object.type == 'MESH':
                meshes.append(obj.data)
                # low level version of apply all modifiers
                object_eval = obj.evaluated_get(depsgraph)
                mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                obj.modifiers.clear()
                obj.data = mesh_from_eval

        ctx = {
            'selected_objects': selected_objects,
            'selected_editable_objects': selected_objects,
            'object': context.active_object,
            'active_object': context.active_object
        }

        if merge is True:
            bpy.ops.object.join(ctx)

        selected_objects = [obj for obj in context.selected_editable_objects if obj.type == 'MESH']

        for obj in selected_objects:
            voxelise(obj)
            if scene_props.fix_non_manifold:
                make_manifold(context, obj)

        for mesh in bpy.data.meshes:
            if mesh is not None:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)

        return {'FINISHED'}


def voxelise(obj):
    """Voxelise the passed in object.

    Args:
        obj (bpy.types.Object): object to be voxelised
    """
    props = bpy.context.scene.mt_scene_props
    obj.data.remesh_voxel_size = props.voxel_size
    obj.data.remesh_voxel_adaptivity = props.voxel_adaptivity

    ctx = {
        'object': obj,
        'active_object': obj,
        'selected_objects': [obj],
        'selected_editable_objects': [obj]}

    bpy.ops.object.voxel_remesh(ctx)
    obj.mt_object_props.geometry_type = 'VOXELISED'


def make_manifold(context, obj):
    """Make the passed in object manifold using the 3dPrint toolkit addon

    Args:
        context (bpy.context): context
        obj (bpy.types.Object): object
    """
    # TODO See if we can speed this up by calling the individual methods of the print3D toolkit
    # check 3d print toolkit is instaleld and active
    if addon_utils.check("object_print3d_utils") == (True, True):
        selected = context.selected_objects
        active = context.active_object
        deselect_all()
        select(obj.name)
        activate(obj.name)
        bpy.ops.mesh.print3d_clean_non_manifold()
        deselect_all()
        for obj in selected:
            select(obj.name)
        activate(active.name)
