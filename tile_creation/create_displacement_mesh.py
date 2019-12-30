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
