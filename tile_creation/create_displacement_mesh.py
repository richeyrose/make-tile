""" Contains functions for turning objects into displacement meshes"""
import os
from math import radians
import bpy
from mathutils import Vector
from .. lib.utils.collections import add_object_to_collection
from .. utils.registration import get_prefs
from .. lib.turtle.scripts.primitives import draw_cuboid
from .. lib.utils.selection import (
    deselect_all,
    select_all,
    select,
    activate)
from .. lib.utils.utils import mode, apply_all_modifiers
from .. lib.utils.vertex_groups import cuboid_sides_to_vert_groups
from .. materials.materials import (
    assign_displacement_materials_2,
    assign_preview_materials_2)
from .. operators.trim_tile import (
    create_tile_trimmers)


def create_displacement_object(obj):
    '''Takes a mesh object and returns a displacement and preview object'''

    preview_obj = obj

    # duplicate preview_obj and make it single user
    displacement_obj = preview_obj.copy()
    displacement_obj.data = displacement_obj.data.copy()  # TODO: Use this method to make objects single user elsewhere

    # add a geometry_type custom property so MakeTile knows that these objects
    # are preview / displacement objects
    preview_obj['geometry_type'] = 'PREVIEW'
    displacement_obj['geometry_type'] = 'DISPLACEMENT'
    add_object_to_collection(displacement_obj, bpy.context.collection.name)
    # make another custom property linking the two objects together
    preview_obj['linked_obj'] = displacement_obj
    displacement_obj['linked_obj'] = preview_obj

    return preview_obj, displacement_obj


def convert_to_make_tile_obj(obj):
    mode('OBJECT')
    # duplicate object and create a second mesh that will be used for adding textures to
    preview_obj, displacement_obj = create_displacement_object(obj)

    # create an empty that we will store properties of our MT object on and
    # which we will parent our objects to
    object_empty = bpy.data.objects.new(obj.name + ".empty", None)
    bpy.context.layer_collection.collection.objects.link(object_empty)
    preview_obj.parent = object_empty
    displacement_obj.parent = object_empty
    object_empty['MT_Properties'] = {
        'textured_groups': {}
    }

    # Get prefs from scene
    prefs = get_prefs()
    material_1 = bpy.data.materials[bpy.context.scene.mt_tile_material_1]
    material_2 = bpy.data.materials[bpy.context.scene.mt_tile_material_2]
    secondary_material = bpy.data.materials[prefs.secondary_material]
    image_size = bpy.context.scene.mt_tile_resolution

    # Check to see if we have any vertex groups already. If not assume we want to
    # add texture to entire object and so create an "All" vertex group and set it
    # to true in object empty properties
    vertex_groups = obj.vertex_groups
    if len(preview_obj.vertex_groups) == 0:
        objs = [preview_obj, displacement_obj]
        for obj in objs:
            group = obj.vertex_groups.new(name="ALL")
            # not sure why we have to do it this way but can't get a list of 
            # keys out in ther normal way
            keys = []
            for key, value in obj.data.vertices.items():
                keys.append(key)
            group.add(keys, 1.0, 'ADD')
            object_empty['MT_Properties']['textured_groups']['ALL'] = True

    assign_displacement_materials_2(
        displacement_obj,
        [image_size, image_size],
        material_1,
        secondary_material)

    assign_preview_materials_2(
        preview_obj,
        material_1,
        secondary_material,
        object_empty['MT_Properties']['textured_groups'])

    displacement_obj.hide_viewport = True

    return preview_obj, displacement_obj
