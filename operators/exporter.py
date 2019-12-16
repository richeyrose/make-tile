import os
import bpy
from .. lib.utils.selection import select, activate, deselect_all, select_all
from .. utils.registration import get_prefs
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

        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        meshes = bpy.context.selected_objects.copy()

        mesh_copies = []

        for mesh in meshes:
            mesh_copy = mesh.copy()
            mesh_copies.append(mesh_copy)
            mesh.hide_viewport = True

        for copy in mesh_copies:
            context.layer_collection.collection.objects.link(copy)

        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                obj.select_set(True)
            obj.select_set(True)

        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', obdata=True)

        for copy in mesh_copies:
            apply_all_modifiers(copy)
        if len(mesh_copies) > 1:
            activate(mesh_copies[0].name)
            bpy.ops.object.join()

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
        bpy.ops.export_mesh.stl('INVOKE_DEFAULT', filepath=file_path, check_existing=True, filter_glob="*.stl", use_selection=True, global_scale=unit_multiplier, use_mesh_modifiers=True)

        for mesh in meshes:
            mesh.hide_viewport = False

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
