import os
import bpy
from .. lib.utils.selection import select, activate, deselect_all, select_all
from .. utils.registration import get_prefs
from .. lib.utils.utils import view3d_find
from .. enums.enums import units
from .voxeliser import voxelise_mesh, apply_all_modifiers


class MT_OT_Export_Tile(bpy.types.Operator):
    """Operator class used to export tiles as .stl"""
    bl_idname = "scene.export_tile"
    bl_label = "Export tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()

        tile_name = context.object.users_collection[0].name

        obs = []
        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                if obj.hide_viewport is False:
                    obs.append(obj)
                    select(obj.name)

        '''
        ctx = bpy.context.copy()
        ctx['active_object'] = obs[0]
        ctx['object'] = obs[0]
        ctx['selected_objects'] = obs
        ctx['selected_editable_objects'] = obs
        '''
        # cannot get this to work with context override whatever I do so using select
        '''
        bpy.ops.object.convert(ctx, target='MESH', keep_original=True)
        '''

        bpy.ops.object.convert(target='MESH', keep_original=True)

        deselect_all()

        for obj in obs:
            obj.hide_viewport = True

        copies = []
        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                if obj.hide_viewport is False:
                    copies.append(obj)

        ctx = bpy.context.copy()
        ctx['active_object'] = copies[0]
        ctx['object'] = copies[0]
        ctx['selected_objects'] = copies
        ctx['selected_editable_objects'] = copies

        bpy.ops.object.join(ctx)

        if bpy.context.scene.mt_voxelise_on_export is True:
            voxelise_mesh(bpy.context.object)

        units = bpy.context.scene.mt_units
        export_path = context.scene.mt_export_path

        if units == 'CM':
            unit_multiplier = 10
        else:
            unit_multiplier = 25.4

        if not os.path.exists(export_path):
            os.mkdir(export_path)
        file_path = os.path.join(context.scene.mt_export_path, tile_name + '.stl')

        deselect_all()
        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                if obj.hide_viewport is False:
                    select(obj.name)

        bpy.ops.export_mesh.stl('INVOKE_DEFAULT', filepath=file_path, check_existing=True, filter_glob="*.stl", use_selection=True, global_scale=unit_multiplier, use_mesh_modifiers=True)

        #TODO: Create merged_tiles collections
        '''
        for obj in obs:
            obj.hide_viewport = False
        '''
        return {'FINISHED'}

    @classmethod
    def register(cls):

        preferences = get_prefs()

        bpy.types.Scene.mt_export_path = bpy.props.StringProperty(
            name="Export Path",
            description="Path to export tiles to",
            subtype="DIR_PATH",
            default=preferences.default_export_path,
        )

        bpy.types.Scene.mt_units = bpy.props.EnumProperty(
            name="Units",
            items=units,
            description="Export units",
            default=preferences.default_units
        )

        bpy.types.Scene.mt_voxelise_on_export = bpy.props.BoolProperty(
            name="Voxelise",
            description="Voxelise on Export.\
                If mesh has been merged this will voxelise everything,\
                otherwise it will just voxelise the displacement meshes",
            default=False
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_voxelise_on_export
        del bpy.types.Scene.mt_units
        del bpy.types.Scene.mt_export_path
