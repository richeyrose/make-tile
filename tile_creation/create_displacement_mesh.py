""" Contains functions for turning objects into displacement meshes"""
import bpy
from .. lib.utils.collections import add_object_to_collection


def create_displacement_object(obj):
    '''Takes a mesh object and returns a displacement and preview object'''

    preview_obj = obj

    # duplicate preview_obj and make it single user
    displacement_obj = preview_obj.copy()
    displacement_obj.data = displacement_obj.data.copy()

    # add a geometry_type custom property so MakeTile knows that these objects
    # are preview / displacement objects
    preview_obj.mt_object_props.geometry_type = 'PREVIEW'
    displacement_obj.mt_object_props.geometry_type = 'DISPLACEMENT'

    add_object_to_collection(displacement_obj, bpy.context.collection.name)

    # make another custom property linking the two objects together
    preview_obj.mt_object_props.linked_object = displacement_obj
    displacement_obj.mt_object_props.linked_object = preview_obj

    return preview_obj, displacement_obj
