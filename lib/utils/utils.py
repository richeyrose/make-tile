from math import radians, sqrt, cos, acos, degrees, isclose
import re
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix
from . selection import select, activate, deselect_all, select_all
from . collections import add_object_to_collection


def set_origin(obj, target_coords=Vector()):
    """Set the origin of the object.

    Args:
        ob (bpy.types.object): object
        target_coords (tuple, optional): coordinates to set origin to. Defaults to Vector().
    """
    mw = obj.matrix_world
    o = mw.inverted() @ Vector(target_coords)
    obj.data.transform(Matrix.Translation(-o))
    mw.translation = target_coords


def get_annotations(cls):
    """Return all annotations of a class including from parent class.

    Returns:
        dict: dict of annotations
    """
    all_annotations = {}
    for c in cls.mro():
        try:
            all_annotations.update(**c.__annotations__)
        except AttributeError:
            # object, at least, has no __annotations__ attribute.
            pass
    return all_annotations


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
    """Return true if two vectors are close to each other.

    Args:
        vec_1 (tuple(float 3)): vector 1
        vec_2 (tuple(float 3)): vector 2
        tolerance (float, optional): tolerance. Defaults to 0.0001.

    Returns:
        bool: true if vectors within tolerance
    """

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


def distance_between_two_points(v1, v2):
    """Return the distance between two point

    Args:
        v1 (tuple(3 float)): location 1
        v2 (tuple(3 float)): location 2

    Returns:
        float: distance bertween v1 and v2
    """
    locx = v2[0] - v1[0]
    locy = v2[1] - v1[1]
    locz = v2[2] - v1[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2)

    return distance


def calc_tri(A, b, c):
    """Return dimensions of triangle.

    Args:
        A (float): Angle A
        b (float): length of side b
        c (float): length of side c

    Returns:
        dict{
            a: length of side a,
            B: angle of corner B,
            C: angle of corner C}: missing dimensions
    """
    #      B
    #      /\
    #   c /  \ a
    #    /    \
    #   /______\
    #  A    b    C
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


def slugify(slug):
    """Return passed in string as a slug suitable for transmission.

    Normalize string, convert to lowercase, remove non-alpha numeric characters,
    and convert spaces to hyphens.
    """
    slug = slug.lower()
    slug = slug.replace('.', '_')
    slug = slug.replace('"', '')
    slug = slug.replace(' ', '_')
    slug = re.sub(r'[^a-z0-9]+.- ', '-', slug).strip('-')
    slug = re.sub(r'[-]+', '-', slug)
    slug = re.sub(r'/', '_', slug)
    return slug
