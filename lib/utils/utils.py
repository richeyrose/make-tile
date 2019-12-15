from math import radians
import bpy
import bmesh
from mathutils import Vector
from . selection import select, activate, deselect_all, select_all


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
    if len(bpy.data.objects) != 0:
        current_mode = bpy.context.object.mode
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


def add_circle_array(obj, circle_center, item_count, axis, degrees_of_arc):
    '''adds a circle array to an object and returns the array name

    Keyword arguments:
    obj -- obj
    circle_center -- VECTOR [X, Y, Z]
    item_count -- INT
    axis -- STR - X, Y, Z
    degrees_of_arc -- FLOAT
    '''
    cursor = bpy.context.scene.cursor
    cursor_orig_location = cursor.location.copy()

    deselect_all()
    select(obj.name)
    activate(obj.name)
    cursor.location = circle_center
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    # add an array modifier
    array_mod = obj.modifiers.new(type='ARRAY', name="circle_array")
    array_mod.use_relative_offset = False
    array_mod.use_object_offset = True
    array_mod.count = item_count

    # create an empty
    circle_origin_empty = bpy.data.objects.new("circle_origin_empty", None)
    bpy.context.scene.collection.objects.link(circle_origin_empty)
    circle_origin_empty.location = circle_center

    # use empty as offset object
    array_mod.offset_object = circle_origin_empty

    # rotate empty
    angle = degrees_of_arc / item_count
    circle_origin_empty.rotation_euler.rotate_axis(axis, radians(angle))

    cursor.location = cursor_orig_location

    return array_mod.name, circle_origin_empty


def apply_all_modifiers(obj):
    """Applies all modifiers in obj"""
    contxt = bpy.context.copy()
    contxt['object'] = obj

    for mod in obj.modifiers[:]:
        contxt['modifier'] = mod
        bpy.ops.object.modifier_apply(
            contxt, apply_as='DATA',
            modifier=contxt['modifier'].name)
