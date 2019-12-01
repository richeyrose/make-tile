import bpy
import bmesh
from mathutils import Vector

C = bpy.context
D = bpy.data


def mode(mode_name):
    """switch modes, ensuring that if we enter edit mode we deselect all selected vertices"""
    if bpy.context.object is None:
        return False
    elif mode_name == bpy.context.object.mode:
        return False
    else:
        bpy.ops.object.mode_set(mode=mode_name)
        if mode_name == "EDIT":
            bpy.ops.mesh.select_all(action="DESELECT")


def delete_all():
    """delete all objects or verts / edges /faces"""
    if len(D.objects) != 0:
        current_mode = C.object.mode
        if current_mode == 'OBJECT':
            select_all()
            bpy.ops.object.delete(use_global=False)
        if current_mode == 'EDIT':
            select_all()
            bpy.ops.mesh.delete()


def delete_object(obj_name):
    """Delete an object by name"""
    select(obj_name)
    bpy.ops.object.delete(use_global=False)


def view3d_find(return_area=False):
    """Returns first 3d view, Normally we get this from context
    need it for loopcut override"""
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    if return_area:
                        return region, rv3d, v3d, area
                    return region, rv3d, v3d
    return None, None
