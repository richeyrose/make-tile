import os
import bpy
from . ut import mode, select_all, deselect_all
from . registration import get_addon_name
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

def make_wall_base(
        tile_system,
        tile_name,
        base_size):
    '''Returns a base for a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain,
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z]
    '''
    #make base
    base = make_cuboid(base_size)
    base.name = tile_name + '.base'

    mode('OBJECT')

    #move base so centred and set origin to world origin
    base.location = (- base_size[0] / 2, - base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #OpenLOCK base options
    if tile_system == 'OPENLOCK':
        
        slot_cutter = make_openlock_base_slot_cutter(base)
        slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
        slot_boolean.operation = 'DIFFERENCE'
        slot_boolean.object = slot_cutter
        slot_cutter.parent = base
        slot_cutter.display_type = 'BOUNDS'

        clip_cutter = make_openlock_base_clip_cutter(base)
        clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
        clip_boolean.operation = 'DIFFERENCE'
        clip_boolean.object = clip_cutter
        clip_cutter.parent = base
        clip_cutter.display_type = 'BOUNDS'

    add_object_to_collection(base, 'Walls')

    return (base)

def make_wall(
        tile_system,
        tile_name,
        tile_size,
        base_size):
    '''Returns the wall part of a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
    #make wall
    wall = make_cuboid([tile_size[0], tile_size[1], tile_size[2] - base_size[2]])
    wall.name = tile_name
    add_object_to_collection(wall, 'Walls')

    mode('OBJECT')

    #move wall so centred, move up so on top of base and set origin to world origin
    wall.location = (-tile_size[0]/2, -tile_size[1] / 2, base_size[2])
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #OpenLOCK wall options
    if tile_system == 'OPENLOCK':
        #check to see if tile is at least 1 inch high
        if tile_size[2] >= 2.53:
            wall_cutters = make_openlock_wall_cutters(wall, tile_size)
            for wall_cutter in wall_cutters:
                wall_cutter.parent = wall
                wall_cutter.display_type = 'BOUNDS'

                wall_cutter_bool = wall.modifiers.new('Wall Cutter', 'BOOLEAN')
                wall_cutter_bool.operation = 'DIFFERENCE'
                wall_cutter_bool.object = wall_cutter

    return (wall)

def make_openlock_wall_cutters(wall, tile_size):
    """Creates the cutters for the wall and positions them correctly
    
    Keyword arguments:
    wall -- wall object
    tile_size --0 [x, y, z] Size of tile including any base but excluding any 
    positive booleans
    """
    deselect_all()

    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.cutter.side", autoselect=True)
    side_cutter1 = bpy.context.selected_objects[0]
    
    add_object_to_collection(side_cutter1, 'Cutters')
    
    wall_location = wall.location
    wall_size = tile_size

    #get location of bottom front left corner of tile
    front_left = [
        wall_location[0] - (wall_size[0] / 2),
        wall_location[1] - (wall_size[1] / 2),
        0]
    #move cutter to bottom front left corner then up by 0.63 inches
    side_cutter1.location = [
        front_left[0],
        front_left[1] + (wall_size[1] / 2),
        front_left[2] + (0.63 * 2.54)]

    array_mod = side_cutter1.modifiers.new('Array', 'ARRAY')
    array_mod.use_relative_offset = False
    array_mod.use_constant_offset = True
    array_mod.constant_offset_displace[2] = 2 * 2.54
    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = wall_size[2] - 2.6

    mirror_mod = side_cutter1.modifiers.new('Mirror', 'MIRROR')
    mirror_mod.use_axis[0] = True
    mirror_mod.mirror_object = wall

    #make a copy of side cutter 1
    side_cutter2 = side_cutter1.copy()
    #link it to cutters collection
    
    add_object_to_collection(side_cutter2, 'Cutters')

    side_cutter2.location[2] = side_cutter2.location[2] + 0.75 * 2.54
    
    array_mod = side_cutter2.modifiers["Array"]
    array_mod.fit_length = wall_size[2] - 4.6

    return [side_cutter1, side_cutter2]

def make_openlock_base_clip_cutter(base):
    """Makes a cutter for the openlock base clip based 
    on the width of the base and positions it correctly

    Keyword arguments:
    object -- base the cutter will be used on
    """
    
    cursor = bpy.context.scene.cursor
    mode('OBJECT')
    base_size = base.dimensions

    #get original location of base and cursor
    base_location = base.location.copy()

    #Get cutter
    deselect_all()
    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip", autoselect=True)
    clip_cutter = bpy.context.selected_objects[0]
    #get start cap
    deselect_all()
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip.cap.start", autoselect=True)
    cutter_start_cap = bpy.context.selected_objects[0]
    #get end cap
    deselect_all()
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip.cap.end", autoselect=True)
    cutter_end_cap = bpy.context.selected_objects[0]

    #get location of bottom front left corner of tile
    front_left = [
        base_location[0] - (base_size[0] / 2),
        base_location[1] - (base_size[1] / 2),
        0]
    
    #move cutter to starting point
    clip_cutter.location = [
        front_left[0] + (0.5 *2.54), 
        front_left[1] + (0.25 * 2.54),
        front_left[2]]

    array_mod = clip_cutter.modifiers.new('Array', 'ARRAY')
    array_mod.start_cap = cutter_start_cap
    array_mod.end_cap = cutter_end_cap
    array_mod.use_merge_vertices = True

    array_mod.fit_type = 'FIT_LENGTH'
    array_mod.fit_length = base_size[0] - 2.54
    
    add_object_to_collection(clip_cutter, 'Cutters')
    add_object_to_collection(cutter_end_cap, 'Cutters')
    add_object_to_collection(cutter_start_cap, 'Cutters')

    return (clip_cutter)


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
        base_dim[0] - ((0.236 * 2) * 2.54),
        0.197 * 2.54,
        0.25 * 2.54]

    cutter = make_cuboid(bool_size)
    cutter.name = base.name + ".cutter.slot"

    mode('OBJECT')

    #move cutter so centred and set cutter origin to world origin + z = -0.01
    # (to avoid z fighting)
    cutter.location = (-bool_size[0] / 2, -0.014 * 2.54, 0)
    cursor.location = [0.0, 0.0, 0.01]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #reset cursor location
    cursor.location = cursor_original_loc

    #set cutter location to base origin
    cutter.location = base_loc

    add_object_to_collection(cutter, 'Cutters')

    return (cutter)

def make_tile(
        tile_units,
        tile_system,
        tile_type,
        bhas_base,
        tile_size,
        base_size):
    """Returns a tile as a collection 

        Keyword arguments:
        tile_system -- which tile system the tile will use. ENUM
        tile_type -- e.g. 'WALL', 'FLOOR', 'DOORWAY', 'ROOF'
        tile_size -- [x, y, z]
        base_size -- if tile has a base [x, y, z]
    """
    scene_collection = bpy.context.scene.collection
    
    #Check to see if tile, cutters, props and greebles
    # collections exist and create if not
    tiles_collection = create_collection('Tiles', scene_collection)
    create_collection('Cutters', scene_collection)
    create_collection('Props', scene_collection)
    create_collection('Greebles', scene_collection)
    
    #TODO: make method return a collection
    #construct tile name based on system and type.
    tile_name = tile_system.lower() + "." + tile_type.lower()

    if tile_units == 'IMPERIAL':
        #Switch unit display to inches
        bpy.context.scene.unit_settings.system = 'IMPERIAL'
        bpy.context.scene.unit_settings.length_unit = 'INCHES'
        bpy.context.scene.unit_settings.scale_length = 0.01

    if tile_type == 'WALL':
        create_collection('Walls', tiles_collection)
        base = make_wall_base(tile_system, tile_name, base_size)
        wall = make_wall(tile_system, tile_name, tile_size, base_size)
        wall.parent = base
        return {'FINISHED'}

    if tile_type == 'FLOOR':
        create_collection('Floors', tiles_collection)
        make_floor(tile_system, tile_name, tile_size)
        return {'FINISHED'}

    return {'CANCELLED'}

def make_floor(
        tile_system,
        tile_name,
        tile_size):
    return {'FINISHED'}
