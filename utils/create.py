import bpy
from . ut import mode, select_all

def make_cuboid(size):
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
    return (bpy.context.object)

def make_wall(
        tile_name,
        tile_size,
        base_size):

    #move cursor to origin
    bpy.context.scene.cursor.location = [0, 0, 0]

    #check if we have a base
    if 0 not in base_size:

        #make base
        base = make_cuboid(base_size)
        base.name = tile_name + '.base'

        mode('OBJECT')

        #move base so centred and set origin to world origin
        base.location = (- base_size[0] / 2, - base_size[1] / 2, 0)
        bpy.context.scene.cursor.location = [0, 0, 0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        #make wall
        wall = make_cuboid([tile_size[0], tile_size[1], tile_size[2] - base_size[2]])
        wall.name = tile_name

        mode('OBJECT')

        #move wall so centred, move up so on top of base and set origin to world origin
        wall.location = (-tile_size[0]/2, -tile_size[1] / 2, base_size[2])
        bpy.context.scene.cursor.location = [0, 0, 0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        #parent wall to base
        wall.parent = base

        return (base, wall)

    #make wall
    wall = make_cuboid(tile_size)
    wall.name = tile_name

    mode('OBJECT')

    #move wall so centred and set origin to world origin
    wall.location = (-tile_size[0]/2, -tile_size[1] / 2, 0.0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    base = False

    return (base, wall)

def make_openlock_base_slot_bool(base_size, base_name):

    #move cursor to origin
    bpy.context.scene.cursor.location = [0, 0, 0]

    #work out bool size from base size
    bool_size = [
        base_size[0] - (0.236 * 2),
        base_size[1] - 0.0787 - 0.236,
        0.25,]

    base_bool = make_cuboid(bool_size)
    base_bool.name = base_name + "cutter.slot"

    #move base_bool so centred and set origin to world origin + z = 0.01 
    # (to avoid z fighting)

    base_bool.location = (-bool_size[0] / 2, -bool_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

def make_tile(
        tile_system,
        tile_type,
        tile_size,
        base_size):

#TODO: change this so all lower case
    tile_name = tile_system.title() + "." + tile_type.title()

    if tile_type == 'WALL':
        make_wall(tile_name, tile_size, base_size)

    elif tile_type == 'FLOOR':
        make_floor(tile_name, tile_size)

    else:
        return False

def make_floor(
        tile_name,
        tile_size):
    return {'FINISHED'}
