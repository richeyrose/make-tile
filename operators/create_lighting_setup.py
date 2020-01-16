import bpy
from .. lib.utils.utils import mode, view3d_find
from .. lib.utils.selection import select, select_all, deselect_all, activate
from .. lib.utils.collections import (
    create_collection,
    add_object_to_collection,
    get_collection,
    activate_collection)
from .. enums.enums import view_mode


class MT_OT_Create_Lighting_Setup(bpy.types.Operator):
    """Creates a lighting setup for Cycles and Eevee previews"""
    bl_idname = "scene.create_lighting_setup"
    bl_label = "Create Lighting"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):
        deselect_all()

        # current_collection
        original_collection = bpy.context.scene.collection.copy()

        # check to see if lighting collection exists and create if not
        scene_collection = bpy.context.scene.collection
        lights_collection = create_collection('Lighting_setup', scene_collection)
        activate_collection(lights_collection.name)

        # Get 3d view
        region, rv3d, v3d, area = view3d_find(True)

        # delete existing lights
        v3d.overlay.show_extras = True
        bpy.ops.object.select_by_type(type='LIGHT')
        bpy.ops.object.delete()

        # add lights
        light_1 = bpy.data.lights.new(name="light_1", type='AREA')
        light_obj = bpy.data.objects.new("front_light_1", light_1)
        bpy.context.layer_collection.collection.objects.link(light_obj)

        light_1.shape = 'RECTANGLE'
        light_1.size = 1
        light_1.size_y = 2
        light_1.energy = 250

        light_obj.location = (-5, -5, 5)
        light_obj.rotation_euler = (1, 0, -0.8)

        light_2 = bpy.data.lights.new(name="light_2", type='AREA')
        light_2_obj = bpy.data.objects.new("front_light_2", light_2)
        bpy.context.layer_collection.collection.objects.link(light_2_obj)

        light_2.shape = 'RECTANGLE'
        light_2.size = 1
        light_2.size_y = 2
        light_2.energy = 50

        light_2_obj.location = (5, -5, -5)
        light_2_obj.rotation_euler = (2.5, 0.8, 1.5)

        light_3 = bpy.data.lights.new(name="light_3", type='AREA')
        light_3_obj = bpy.data.objects.new("back_light_1", light_3)
        bpy.context.layer_collection.collection.objects.link(light_3_obj)

        light_3.shape = 'RECTANGLE'
        light_3.size = 1
        light_3.size_y = 2
        light_3.energy = 250

        light_3_obj.location = (-5, 5, 5)
        light_3_obj.rotation_euler = (1, 0, -2.3)

        light_4 = bpy.data.lights.new(name="light_4", type='AREA')
        light_4_obj = bpy.data.objects.new("back_light_2", light_4)
        bpy.context.layer_collection.collection.objects.link(light_4_obj)

        light_4.shape = 'RECTANGLE'
        light_4.size = 1
        light_4.size_y = 2
        light_4.energy = 50

        light_4_obj.location = (5, 5, -5)
        light_4_obj.rotation_euler = (2.5, 0.8, 3)

        if bpy.context.scene.mt_view_mode == 'CYCLES':
            v3d.shading.type = 'RENDERED'
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.space_data.shading.use_scene_world_render = True
            bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'

        if bpy.context.scene.mt_view_mode == 'EEVEE':
            v3d.shading.type = 'RENDERED'
            bpy.context.scene.render.engine = 'BLENDER_EEVEE'
            bpy.context.space_data.shading.use_scene_world_render = False
            bpy.context.space_data.shading.studio_light = 'night.exr'

        if bpy.context.scene.mt_view_mode == 'PREVIEW':
            v3d.shading.type = 'MATERIAL'

        # hide "extras" i.e lights and camera lines
        v3d.overlay.show_extras = False

        # switch back to original collection
        activate_collection(original_collection.name)

        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        bpy.types.Scene.mt_use_gpu = bpy.props.BoolProperty(
            name="Use GPU",
            description="Use GPU for Cycles render",
            default=True,
        )

        bpy.types.Scene.mt_cycles_subdivision_quality = bpy.props.IntProperty(
            name="Subdivision",
            description="Cycles subdivision - higher = higher quality.",
            default=1,
        )

        bpy.types.Scene.mt_view_mode = bpy.props.EnumProperty(
            items=view_mode,
            name="Render Engine",
            default="CYCLES",
            update=update_view_mode,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_view_mode
        del bpy.types.Scene.mt_cycles_subdivision_quality
        del bpy.types.Scene.mt_use_gpu


def update_view_mode(self, context):
    region, rv3d, v3d, area = view3d_find(True)

    if bpy.context.scene.mt_view_mode == 'CYCLES':
        v3d.shading.type = 'RENDERED'
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.space_data.shading.use_scene_world_render = True
        bpy.context.scene.cycles.feature_set = 'EXPERIMENTAL'

        if bpy.context.scene.mt_use_gpu is True:
            bpy.context.scene.cycles.device = 'GPU'

    if bpy.context.scene.mt_view_mode == 'EEVEE':
        v3d.shading.type = 'RENDERED'
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.space_data.shading.use_scene_world_render = False
        bpy.context.space_data.shading.studio_light = 'night.exr'

    if bpy.context.scene.mt_view_mode == 'PREVIEW':
        v3d.shading.type = 'MATERIAL'
