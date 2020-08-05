from math import radians, sqrt, cos, acos, degrees, isclose
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix
from . selection import select, activate, deselect_all, select_all
from . collections import add_object_to_collection


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


def add_circle_array(obj, tile_name, circle_center, item_count, axis, degrees_of_arc):
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
    add_object_to_collection(circle_origin_empty, tile_name)
    circle_origin_empty.location = circle_center

    # use empty as offset object
    array_mod.offset_object = circle_origin_empty

    # rotate empty
    angle = degrees_of_arc
    circle_origin_empty.rotation_euler.rotate_axis(axis, radians(angle))

    cursor.location = cursor_orig_location

    return array_mod.name, circle_origin_empty


def get_tile_props(obj):
    tile_name = obj.mt_object_props.tile_name
    tile_props = bpy.data.collections[tile_name].mt_tile_props
    return tile_props


def loopcut_and_add_deform_modifiers(obj, segments=8, degrees_of_arc=90, axis='Z', show_render=False):
    # uses loopcut to subdivide a mesh and adds a deform modifier
    deselect_all()
    select(obj.name)
    activate(obj.name)

    # loopcut
    mode('EDIT')
    region, rv3d, v3d, area = view3d_find(True)

    override = {
        'scene': bpy.context.scene,
        'region': region,
        'area': area,
        'space': v3d
    }

    bpy.ops.mesh.loopcut(
        override,
        number_cuts=segments - 2,
        smoothness=0,
        falloff='INVERSE_SQUARE',
        object_index=0,
        edge_index=2)

    mode('OBJECT')

    curve_mod = obj.modifiers.new("curve", "SIMPLE_DEFORM")
    curve_mod.deform_method = 'BEND'
    curve_mod.deform_axis = axis
    curve_mod.show_render = show_render
    curve_mod.angle = radians(degrees_of_arc)

    return curve_mod


def distance_between_two_verts(first, second):
    '''returns the distance between 2 verts'''
    locx = second[0] - first[0]
    locy = second[1] - first[1]
    locz = second[2] - first[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)
    return distance


def calc_tri(A, b, c):
    '''returns full dimensions of triangle given 1 angle and 2 sides'''
    a = sqrt((b**2 + c**2) - ((2 * b * c) * cos(radians(A))))
    B = degrees(acos((c**2 + a**2 - (b**2)) / (2 * c * a)))
    C = 180 - A - B

    dimensions = {
        'a': a,
        'b': b,
        'c': c,
        'A': A,
        'B': B,
        'C': C}

    return dimensions


def clear_parent_and_apply_transformation(ctx, ob):
    #ob = bpy.context.object
    mat = ob.matrix_world

    loc, rot, sca = mat.decompose()

    mat_loc = Matrix.Translation(loc)
    mat_rot = rot.to_matrix().to_4x4()
    mat_sca = Matrix.Identity(4)
    mat_sca[0][0], mat_sca[1][1], mat_sca[2][2] = sca

    mat_out = mat_loc @ mat_rot @ mat_sca
    mat_h = mat_out.inverted() @ mat

    # Move the vertices to their original position,
    # which the mat_out can't represent.
    for v in ob.data.vertices:
        v.co = mat_h @ v.co


def vectors_are_close(vec_1, vec_2, tolerance=0.0001):
    '''Tests whether two vectors are almost equal to each other'''
    return isclose(vec_1[0], vec_2[0], abs_tol=tolerance) and \
        isclose(vec_1[1], vec_2[1], abs_tol=tolerance) and \
        isclose(vec_1[2], vec_2[2], abs_tol=tolerance)


def get_all_subclasses(python_class):
    """
    Helper function to get all the subclasses of a class.
    :param python_class: Any Python class that implements __subclasses__()
    """
    python_class.__subclasses__()

    subclasses = set()
    check_these = [python_class]

    while check_these:
        parent = check_these.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                check_these.append(child)

    return sorted(subclasses, key=lambda x: x.__name__)