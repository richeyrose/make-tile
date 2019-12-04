import os
import bpy
from .. lib.utils.selection import select, activate, deselect_all, select_all
from .. utils.registration import get_prefs
from .. enums.enums import units


class MT_OT_Tile_Voxeliser(bpy.types.Operator):
    """Operator class used to voxelise tiles"""
    bl_idname = "scene.voxelise_tile"
    bl_label = "Voxelise tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()
        bpy.ops.object.select_by_type(type='MESH')
        meshes = bpy.context.selected_objects.copy()

        if context.scene.mt_merge_and_voxelise is True:
            for mesh in meshes:
                apply_all_modifiers(mesh)
            if len(meshes) > 1:
                bpy.ops.object.join()
            voxelise_mesh(bpy.context.object)
        else:
            # apply all displacement modifiers
            for mesh in meshes:
                if 'geometry_type' in mesh:
                    if mesh['geometry_type'] == 'DISPLACEMENT':
                        apply_all_modifiers(mesh)
                        voxelise_mesh(mesh)

        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_voxel_quality = bpy.props.FloatProperty(
            name="Quality",
            description="Quality of the voxelisation. Smaller = Better",
            soft_min=0.005,
            default=0.005,
            precision=3,

        )

        bpy.types.Scene.mt_voxel_adaptivity = bpy.props.FloatProperty(
            name="Adaptivity",
            description="Amount by which to simplify mesh",
            default=0.01,
            precision=3,
        )

        bpy.types.Scene.mt_merge_and_voxelise = bpy.props.BoolProperty(
            name="Merge",
            description="Merge tile before voxelising? Creates a single mesh.",
            default=True
        )


    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_merge_and_voxelise
        del bpy.types.Scene.mt_voxel_adaptivity
        del bpy.types.Scene.mt_voxel_quality


class MT_OT_Export_Tile(bpy.types.Operator):
    """Operator class used to export tiles"""
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
        # TODO: Implement overwrite option
        deselect_all()
        bpy.ops.object.select_by_type(type='MESH')
        meshes = bpy.context.selected_objects.copy()
        mesh_copies = []

        for mesh in meshes:
            mesh_copy = mesh.copy()
            mesh_copies.append(mesh_copy)
            mesh.hide_viewport = True

        for copy in mesh_copies:
            context.layer_collection.collection.objects.link(copy)

        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', obdata=True)

        for copy in mesh_copies:
            apply_all_modifiers(copy)

        if bpy.context.scene.mt_merge_on_export is True:
            if len(mesh_copies) > 1:
                activate(mesh_copies[0].name)
                bpy.ops.object.join()

        if bpy.context.scene.mt_voxelise_on_export is True:
            if bpy.context.scene.mt_merge_on_export is True:
                voxelise_mesh(bpy.context.object)
            else:
                for copy in mesh_copies:
                    if 'geometry_type' in copy:
                        if copy['geometry_type'] == 'DISPLACEMENT':
                            apply_all_modifiers(copy)
                            voxelise_mesh(copy)

        units = bpy.context.scene.mt_units
        export_path = context.scene.mt_export_path

        if units == 'CM':
            unit_multiplier = 10
        else:
            unit_multiplier = 25.4

        if not os.path.exists(export_path):
            os.mkdir(export_path)

        file_path = os.path.join(context.scene.mt_export_path, context.scene.mt_tile_name + '.stl')
        bpy.ops.export_mesh.stl(filepath=file_path, check_existing=True, filter_glob="*.stl", use_selection=True, global_scale=unit_multiplier, use_mesh_modifiers=True)

        bpy.ops.object.delete()
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

        bpy.types.Scene.mt_merge_on_export = bpy.props.BoolProperty(
            name="Merge",
            description="Merge all meshes on export",
            default=False,
        )

        bpy.types.Scene.mt_voxelise_on_export = bpy.props.BoolProperty(
            name="Voxelise",
            description="Voxelise on Export.\
                If mesh has been merged this will voxelise everything,\
                otherwise it will just voxelise the displacement meshes",
            default=False
        )

        bpy.types.Scene.mt_tile_name = bpy.props.StringProperty(
            name="Tile Export Name",
            description="Name to save tile as",
            default="Tile"
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_tile_name
        del bpy.types.Scene.mt_voxelise_on_export
        del bpy.types.Scene.mt_merge_on_export
        del bpy.types.Scene.mt_units
        del bpy.types.Scene.mt_export_path


def voxelise_mesh(mesh):
    activate(mesh.name)
    mesh.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
    mesh.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity
    bpy.ops.object.voxel_remesh()


def apply_all_modifiers(mesh):
    contxt = bpy.context.copy()
    contxt['object'] = mesh

    for mod in mesh.modifiers[:]:
        contxt['modifier'] = mod
        bpy.ops.object.modifier_apply(
            contxt, apply_as='DATA',
            modifier=contxt['modifier'].name
        )
