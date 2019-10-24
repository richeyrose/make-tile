import os
import bpy
from . ut import mode, select_all, deselect_all, select, activate
from . registration import get_path
from . collections import create_collection, add_object_to_collection

def make_cuboid(size):
    """Returns a cuboid"""
    #add vert
    bpy.ops.mesh.primitive_vert_add()

    #extrude vert along X
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False},
        TRANSFORM_OT_translate=
        {"value":(size[0], 0, 0),
         "orient_type":'GLOBAL',
         "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         "orient_matrix_type":'GLOBAL',
         "constraint_axis":(True, False, False),
         "mirror":False,
         "use_proportional_edit":False,
         "snap":False,
         "gpencil_strokes":False,
         "cursor_transform":False,})

    select_all()

    #extrude edge along Y
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={
            "use_normal_flip":False, "mirror":False},
        TRANSFORM_OT_translate=
        {"value":(0, size[1], 0),
         "orient_type":'GLOBAL',
         "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         "orient_matrix_type":'GLOBAL',
         "constraint_axis":(False, True, False),
         "mirror":False,
         "use_proportional_edit":False,
         "snap":False,
         "gpencil_strokes":False,
         "cursor_transform":False,})

    select_all()

    #extrude face along Z
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False},
        TRANSFORM_OT_translate=
        {"value":(0, 0, size[2]),
         "orient_type":'GLOBAL',
         "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         "orient_matrix_type":'GLOBAL',
         "constraint_axis":(False, False, True),
         "mirror":False,
         "use_proportional_edit":False,
         "snap":False,
         "gpencil_strokes":False,
         "cursor_transform":False,})
    return bpy.context.object