import bpy
from . selection import select_by_loc, deselect_all
from . utils import mode


def cuboid_sides_to_vert_groups():
    """makes a vertex group for each side of cuboid
    and assigns vertices to it"""

    mode('OBJECT')
    obj = bpy.context.object
    dim = obj.dimensions / 2

    # get original location of object origin and of cursor
    obj_original_loc = obj.location.copy()
    cursor_original_loc = bpy.context.scene.cursor.location.copy()

    # set origin to center of bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # make vertex groups
    obj.vertex_groups.new(name='x_neg')
    obj.vertex_groups.new(name='x_pos')
    obj.vertex_groups.new(name='y_neg')
    obj.vertex_groups.new(name='y_pos')
    obj.vertex_groups.new(name='z_neg')
    obj.vertex_groups.new(name='z_pos')

    mode('EDIT')

    # select x_neg and assign to x_neg
    select_by_loc(
        lbound=-dim,
        ubound=[-dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)

    bpy.ops.object.vertex_group_set_active(group='x_neg')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select x_pos and assign to x_pos
    select_by_loc(
        lbound=[dim[0], -dim[1], -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='x_pos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select y_neg and assign to y_neg
    select_by_loc(
        lbound=-dim,
        ubound=[dim[0], -dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='y_neg')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select y_pos and assign to y_pos
    select_by_loc(
        lbound=[-dim[0], dim[1], -dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='y_pos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select z_neg and assign to z_neg
    select_by_loc(
        lbound=-dim,
        ubound=[dim[0], dim[1], -dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='z_neg')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    # select z_pos and assign to z_pos
    select_by_loc(
        lbound=[-dim[0], -dim[1], dim[2]],
        ubound=[dim[0], dim[1], dim[2]],
        select_mode='VERT',
        coords='LOCAL',
        additive=True)
    bpy.ops.object.vertex_group_set_active(group='z_pos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    mode('OBJECT')

    # reset cursor and object origin
    bpy.context.scene.cursor.location = obj_original_loc
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.context.scene.cursor.location = cursor_original_loc
