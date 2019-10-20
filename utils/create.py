import os
import bpy
from . ut import mode, select_all, deselect_all
from . registration import get_addon_name
from . registration import get_path

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

#TODO: make seperate make_wall_base method and ensure this only returns wall
def make_wall(
        tile_system,
        tile_name,
        tile_size,
        base_size):
    '''Makes a wall tile and returns bot it and the base if a base is created.

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
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

        '''OpenLOCK base options'''
        if tile_system == 'OPENLOCK':
            slot_cutter = make_openlock_base_slot_cutter(base)
            slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
            slot_boolean.object = slot_cutter
            slot_cutter.parent = base
            slot_cutter.display_type = 'BOUNDS'

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

        #OpenLOCK wall options
        if tile_system == 'OPENLOCK':
            
            deselect_all()

            booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")
            bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.cutter.side", autoselect=True)
            side_cutter = bpy.context.selected_objects[0]     

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

def make_openlock_base_slot_cutter(base):
    """Makes a cutter for the openlock base slot
    based on the width of the base

    Keyword arguments:
    object -- base the cutter will be used on
    """
    cursor = bpy.context.scene.cursor
    mode('OBJECT')
    base_dim = base.dimensions

    #get original location of object and cursor
    base_loc = base.location.copy()
    cursor_original_loc = cursor.location.copy()

    #move cursor to origin
    cursor.location = [0, 0, 0]

    #work out bool size X from base size, y and z are constants
    bool_size = [
        base_dim[0] - (0.236 * 2),
        0.197,
        0.25,]

    cutter = make_cuboid(bool_size)
    cutter.name = base.name + ".cutter.slot"

    mode('OBJECT')

    #move cutter so centred and set cutter origin to world origin + z = -0.01
    # (to avoid z fighting)
    cutter.location = (-bool_size[0] / 2, -0.014, 0)
    cursor.location = [0.0, 0.0, 0.01]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #reset cursor location
    cursor.location = cursor_original_loc

    #set cutter location to base origin
    cutter.location = base_loc

    return (cutter)

def make_tile(
        tile_system,
        tile_type,
        tile_size,
        base_size):
    """spawns a tile at world origin.

        Keyword arguments:
        tile_system -- which tile system the tile will use. ENUM
        tile_type -- e.g. 'WALL', 'FLOOR', 'DOORWAY', 'ROOF'
        tile_size -- [x, y, z]
        base_size -- if tile has a base [x, y, z]
    """
    #TODO: check to see if tile, cutters, props and greebles
    # collections exist and create if not
    tile_name = tile_system.lower() + "." + tile_type.lower()

    if tile_type == 'WALL':
        make_wall(tile_system, tile_name, tile_size, base_size)
        return {'FINISHED'}

    elif tile_type == 'FLOOR':
        make_floor(tile_system, tile_name, tile_size)
        return {'FINSIHED'}

    else:
        return False

def make_floor(
        tile_system,
        tile_name,
        tile_size):
    return {'FINISHED'}
