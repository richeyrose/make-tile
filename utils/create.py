import bpy
import os
from .. utils.ut import mode, select_all


def make_cuboid(size = [1.0, 1.0, 0.5]):
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
    MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, 
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


def make_wall(
    tile_name = 'Wall',
    tile_size = [2.0, 0.5, 2.0],
    base_size = [2.0, 0.5, 0.3]):
        
    #move cursor to origin
    bpy.context.scene.cursor.location = [0,0,0]
    
    #check if we have a base
    if 0 not in base_size:
        
        #make base
        make_cuboid(base_size)
        base = bpy.context.object
        base.name = tile_name + '.Base'
        
        mode('OBJECT')
        
        #move base so centred and set origin to world origin
        base.location =(- base_size[0] / 2, - base_size[1] / 2, 0)
        bpy.context.scene.cursor.location = [0,0,0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        
        #subtract base height from overall tile height
        tile_size[2] = tile_size[2]- base_size[2]
        
        #make wall
        make_cuboid(tile_size)
        wall = bpy.context.object
        wall.name = tile_name
            
        mode('OBJECT')
        
        #move wall so centred, move up so on top of base and set origin to world origin
        wall.location =(-tile_size[0]/2, -tile_size[1] / 2, base_size[2])
        bpy.context.scene.cursor.location = [0,0,0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        #parent wall to base
        wall.parent = base
        
        return (base, wall)
    
    else:
        
        #make wall
        make_cuboid(tile_size)
        wall = bpy.context.object
        wall.name = tile_name
            
        mode('OBJECT')
        
        #move wall so centred and set origin to world origin
        wall.location =(-tile_size[0]/2, -tile_size[1] / 2, 0.0) 
        bpy.context.scene.cursor.location = [0,0,0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        
        base = False
        
        return (base, wall)

def make_tile(
    tile_system = 'OPENLOCK', 
    tile_type = 'WALL', 
    tile_name = 'Wall', 
    tile_size = [2.0, 0.5, 2.0], 
    base_size = [0.0, 0.0, 0.0]):
    
    if tile_type == 'WALL':
        make_wall(tile_name, tile_size, base_size)
        
    elif tile_type == 'FLOOR':
        make_floor(tile_size)
        
    else:
        return False

def make_floor(
    tile_size = [2.0, 2.0, 0.3]):
    return {'FINISHED'}