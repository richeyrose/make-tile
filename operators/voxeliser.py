import bpy
from .. lib.utils.selection import select, deselect_all, select_all, activate


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

        for obj in context.layer_collection.collection.all_objects:
            if obj.type == 'MESH':
                obj.select_set(True)
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


def voxelise_mesh(obj):
    """Voxelises the passed in object
    Keyword Arguments:
    obj -- MESH OBJECT
    """

    obj.data.remesh_voxel_size = bpy.context.scene.mt_voxel_quality
    obj.data.remesh_voxel_adaptivity = bpy.context.scene.mt_voxel_adaptivity
    bpy.ops.object.voxel_remesh()
    obj.modifiers.new('Triangulate', 'TRIANGULATE')

    return obj


def apply_all_modifiers(mesh, only_visible=True):
    '''Applies all modifiers. if only_vsible is True it only applies those
    modifiers that are visible in the viewport'''
    contxt = bpy.context.copy()
    contxt['object'] = mesh

    for mod in mesh.modifiers[:]:
        contxt['modifier'] = mod

        if only_visible is True:
            if contxt['modifier'].show_viewport is True:
                bpy.ops.object.modifier_apply(
                    contxt, apply_as='DATA',
                    modifier=contxt['modifier'].name)
        else:
            bpy.ops.object.modifier_apply(
                contxt, apply_as='DATA',
                modifier=contxt['modifier'].name)