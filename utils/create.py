import bpy
import os
from .. utils.ut import mode, select_all, deselect_all
from .. utils.selection import select_by_loc

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

#makes a vertex group for each face of cuboid
# and assigns vertices to it
def cuboid_face_to_vert_groups():
    
    ob = bpy.context.object
    dimensions = ob.dimensions
    mode('EDIT')

    #make vertex groups
    XNeg = ob.vertex_groups.new(name='XNeg')    
    XPos = ob.vertex_groups.new(name='XPos')
    YNeg = ob.vertex_groups.new(name='YNeg')
    YPos = ob.vertex_groups.new(name='YPos')
    ZNeg = ob.vertex_groups.new(name='ZNeg')
    ZPos = ob.vertex_groups.new(name='ZPos')

    #select XNeg and assign to XNeg
    select_by_loc(
        lbound = [0.0,0.0,0.0],
        ubound = [0.0, dimensions[1], dimensions[2]],
        select_mode = 'VERT',
        coords = 'LOCAL',
        additive = True)

    bpy.ops.object.vertex_group_set_active(group = 'XNeg')
    bpy.ops.object.vertex_group_assign()    

    deselect_all()

    #select XPos and assign to XPos
    select_by_loc(
        [dimensions[0],0.0,0.0], 
        [dimensions[0], dimensions[1], dimensions[2]])
    bpy.ops.object.vertex_group_set_active(group ='XPos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    #select YNeg and assign to YNeg
    select_by_loc(
        [0.0,0.0,0.0], 
        [dimensions[0], 0, dimensions[2]])
    bpy.ops.object.vertex_group_set_active(group ='YNeg')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    #select YPos and assign to YPos
    select_by_loc(
        [0.0,dimensions[1],0.0], 
        [dimensions[0], dimensions[1], dimensions[2]])
    bpy.ops.object.vertex_group_set_active(group ='YPos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    #select ZNeg and assign to ZNeg
    select_by_loc(
        [0.0,0.0,0.0], 
        [dimensions[0], dimensions[1], 0.0])
    bpy.ops.object.vertex_group_set_active(group ='ZNeg')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

    #select ZPos and assign to ZPos
    select_by_loc(
        [0.0,0.0,dimensions[2]], 
        [dimensions[0], dimensions[1], dimensions[2]])
    bpy.ops.object.vertex_group_set_active(group ='ZPos')
    bpy.ops.object.vertex_group_assign()

    deselect_all()

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
        
        cuboid_face_to_vert_groups()

        mode('OBJECT')
        
        #move base so centred and set origin to world origin
        base.location =(- base_size[0] / 2, - base_size[1] / 2, 0)
        bpy.context.scene.cursor.location = [0,0,0]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
          
        #make wall
        make_cuboid([tile_size[0], tile_size[1], tile_size[2] - base_size[2]])
        wall = bpy.context.object
        wall.name = tile_name
        
        cuboid_face_to_vert_groups()

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

        cuboid_face_to_vert_groups()

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