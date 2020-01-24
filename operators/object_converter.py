import bpy
from .. tile_creation.create_displacement_mesh import create_displacement_object
from .. lib.utils.utils import mode
from .. utils.registration import get_prefs
from .. materials.materials import assign_displacement_materials, assign_mat_to_vert_group
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)


# TODO: Fix bug with object creation not working if you delete default cube, add an object and try to convert that object wothout first creating a tile
class MT_OT_Convert_To_MT_Obj(bpy.types.Operator):
    '''Convert a mesh into a MakeTile object'''
    bl_idname = "object.convert_to_make_tile"
    bl_label = "Convert to MakeTile object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH'})

    def execute(self, context):
        obj = context.object
        self.convert_to_make_tile_obj(obj)
        return {'FINISHED'}

    def convert_to_make_tile_obj(self, obj):
        mode('OBJECT')
        # duplicate object and create a second mesh that will be used for adding textures to
        preview_obj, displacement_obj = create_displacement_object(obj)

        # create an empty that we will store properties of our MT object on and
        # which we will parent our objects to
        object_empty = bpy.data.objects.new(obj.name + ".empty", None)
        bpy.context.layer_collection.collection.objects.link(object_empty)
        preview_obj.parent = object_empty
        displacement_obj.parent = object_empty
        object_empty['MT_Properties'] = {}

        # Get prefs from scene
        prefs = get_prefs()
        material_1 = bpy.data.materials[bpy.context.scene.mt_tile_material_1]
        material_2 = bpy.data.materials[bpy.context.scene.mt_tile_material_2]
        secondary_material = bpy.data.materials[prefs.secondary_material]
        image_size = bpy.context.scene.mt_tile_resolution

        # Check to see if we have any vertex groups already. If not assume we want to
        # add texture to entire object and so create an "All" vertex group and set it
        # to true in objects mt_textured_areas_coll
        if len(preview_obj.vertex_groups) == 0:
            objs = [preview_obj, displacement_obj]
            for obj in objs:
                group = obj.vertex_groups.new(name="ALL")
                deselect_all()
                select(obj.name)
                mode('EDIT')
                select_all()
                bpy.ops.object.vertex_group_set_active(group='ALL')
                bpy.ops.object.vertex_group_assign()
                deselect_all()
                mode('OBJECT')

        vert_groups = preview_obj.vertex_groups

        '''
        for group in vert_groups:
            collectionItem = preview_obj.mt_textured_areas_coll.add()
            collectionItem.value = False
            collectionItem.name = group.name

        # assign material to vertex group
        if 'ALL' in preview_obj.mt_textured_areas_coll.keys():
            for key, value in preview_obj.mt_textured_areas_coll.items():
                if key == 'ALL':
                    value.value = True
        '''

        assign_displacement_materials(
            displacement_obj,
            [image_size, image_size],
            material_1,
            secondary_material)

        displacement_obj.hide_viewport = True

        return preview_obj, displacement_obj

