""" Contains functions for creating wall tiles """
import os
import bpy
from .. utils.collections import add_object_to_collection
from .. utils.ut import mode, deselect_all, select, activate
from .. utils.registration import get_path
from .. utils.create import make_cuboid

def make_straight_wall(
        tile_system,
        tile_name,
        tile_size,
        base_size,
        base_system,
        bhas_base):
    """Returns a straight wall
    Keyword arguments:
    tile_system -- tile system for slabs
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z],
    base_system -- tile system for bases
    bhas_base --- whether tile has a seperate base
    """

    if bhas_base:
        base = make_straight_wall_base(
            base_system,
            tile_name,
            base_size)
        wall = make_straight_wall_slab(
            tile_system,
            tile_name,
            tile_size,
            base_size)
        base.parent = wall
        return wall

    wall = make_straight_wall_slab(tile_system, tile_name, tile_size, base_size)
    return wall

def make_straight_wall_base(
        base_system,
        tile_name,
        base_size):
    """Returns a base for a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain,
    tile_name   -- name,
    tile_size   -- [x, y, z],
    base_size   -- [x, y, z]
    """
    
    #make base
    base_mesh = bpy.data.meshes.new("base_mesh")
    base = bpy.data.objects.new(tile_name + '.base', base_mesh)
    add_object_to_collection(base, tile_name)
    select(base.name)
    activate(base.name)
    
    mode('EDIT')
    base = make_cuboid(base_size)
    mode('OBJECT') 

    #move base so centred and set origin to world origin
    base.location = (- base_size[0] / 2, - base_size[1] / 2, 0)
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #OpenLOCK base options
    if base_system == 'OPENLOCK':
        make_openlock_straight_wall_base(base, tile_name) 

    return (base)

def make_openlock_straight_wall_base(straight_wall_base, tile_name):
    """takes a straight wall base and makes it into an openlock style base"""
    base = straight_wall_base
    slot_cutter = make_openlock_base_slot_cutter(base, tile_name)
    slot_boolean = base.modifiers.new(slot_cutter.name, 'BOOLEAN')
    slot_boolean.operation = 'DIFFERENCE'
    slot_boolean.object = slot_cutter
    slot_cutter.parent = base
    slot_cutter.display_type = 'BOUNDS'

    clip_cutter = make_openlock_base_clip_cutter(base, tile_name)
    clip_boolean = base.modifiers.new(clip_cutter.name, 'BOOLEAN')
    clip_boolean.operation = 'DIFFERENCE'
    clip_boolean.object = clip_cutter
    clip_cutter.parent = base
    clip_cutter.display_type = 'BOUNDS'

def make_straight_wall_slab(
        tile_system,
        tile_name,
        tile_size,
        base_size):
    '''Returns the slab part of a wall tile

    Keyword arguments:
    tile_system -- What tile system to usee e.g. OpenLOCK, DragonLOCK, plain
    tile_name   -- name
    tile_size   -- [x, y, z]
    base_size   -- [x, y, z]
    '''
    slab_mesh = bpy.data.meshes.new("slab_mesh")
    slab = bpy.data.objects.new(tile_name + ".slab", slab_mesh)
    add_object_to_collection(slab, tile_name)
    select(slab.name)
    activate(slab.name)

    mode('EDIT')

    slab = make_cuboid([
        tile_size[0],
        tile_size[1],
        tile_size[2] - base_size[2]])

    mode('OBJECT')

    #move slab so centred, move up so on top of base and set origin to world origin
    slab.location = (-tile_size[0]/2, -tile_size[1] / 2, base_size[2])
    bpy.context.scene.cursor.location = [0, 0, 0]
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    #OpenLOCK wall options
    if tile_system == 'OPENLOCK':
        #check to see if tile is at least 1 inch high
        if tile_size[2] >= 2.53:
            wall_cutters = make_openlock_wall_cutters(slab, tile_size, tile_name)
            for wall_cutter in wall_cutters:
                wall_cutter.parent = slab
                wall_cutter.display_type = 'BOUNDS'

                wall_cutter_bool = slab.modifiers.new('Wall Cutter', 'BOOLEAN')
                wall_cutter_bool.operation = 'DIFFERENCE'
                wall_cutter_bool.object = wall_cutter

    return (slab)

def make_openlock_wall_cutters(wall, tile_size, tile_name):
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
    add_object_to_collection(side_cutter1, tile_name)

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
    add_object_to_collection(side_cutter2, tile_name)

    side_cutter2.location[2] = side_cutter2.location[2] + 0.75 * 2.54

    array_mod = side_cutter2.modifiers["Array"]
    array_mod.fit_length = wall_size[2] - 4.6

    return [side_cutter1, side_cutter2]

def make_openlock_base_clip_cutter(base, tile_name):
    """Makes a cutter for the openlock base clip based 
    on the width of the base and positions it correctly

    Keyword arguments:
    object -- base the cutter will be used on
    """
    
    mode('OBJECT')
    base_size = base.dimensions

    #get original location of base and cursor
    base_location = base.location.copy()

    #Get cutter
    deselect_all()
    booleans_path = os.path.join(get_path(), "assets", "meshes", "booleans", "openlock.blend")
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip", autoselect=True)
    clip_cutter = bpy.context.selected_objects[0]
    add_object_to_collection(clip_cutter, tile_name)
    #get start cap
    deselect_all()
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip.cap.start", autoselect=True)
    cutter_start_cap = bpy.context.selected_objects[0]
    add_object_to_collection(cutter_start_cap, tile_name)
    #get end cap
    deselect_all()
    bpy.ops.wm.append(directory=booleans_path + "\\Object\\", filename="openlock.wall.base.cutter.clip.cap.end", autoselect=True)
    cutter_end_cap = bpy.context.selected_objects[0]
    add_object_to_collection(cutter_end_cap, tile_name)

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
    
    return (clip_cutter)

def make_openlock_base_slot_cutter(base, tile_name):
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

    cutter_mesh = bpy.data.meshes.new("cutter_mesh")
    cutter = bpy.data.objects.new(tile_name + ".cutter.slot", cutter_mesh)
    add_object_to_collection(cutter, tile_name)
    select(cutter.name)
    activate(cutter.name)

    mode('EDIT')
    cutter = make_cuboid(bool_size)
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

    return (cutter)