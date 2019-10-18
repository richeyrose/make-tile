import bpy
import bmesh
from mathutils import Vector

#gets local object center relative to origin
def get_local_bbox_center(obj):
    local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    return local_bbox_center

#gets global object center
def get_global_bbox_center(obj):
    local_bbox_center = get_local_bbox_center(obj)
    global_bbox_center = obj.matrix_world @ local_bbox_center
    return global_bbox_center

#lbound = lowest left of cuboid
#ubound = upper right of cuboid
def in_bbox(lbound, ubound, v, buffer=0.0001):
    return lbound[0]-buffer <=v[0]<=ubound[0]+buffer and \
    lbound[1]-buffer<=v[1]<=ubound[1]+buffer and \
    lbound[2]-buffer<=v[2]<=ubound[2]+buffer

def select_by_loc(
        lbound=(0, 0, 0), 
        ubound=(0, 0, 0), 
        select_mode='VERT', 
        coords='GLOBAL', 
        additive=True):
    #set selection mode
    bpy.ops.mesh.select_mode(type=select_mode)
    #grab the transformation matrix
    world = bpy.context.object.matrix_world

    #instantiate a bmesh object and ensure lookup table (bm.faces.ensure... works for all)
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()

    #initialise list of verts and parts to be selected
    verts = []
    to_select = []

    #for VERT, EDGE or FACE
        #grab list of global or local coords
        #test if the piece is entirely within the rectangular
        #prism defined by lbound and ubound
        #select each piece that returned TRUE and deselect each piece that returned FALSE
        
    if select_mode == 'VERT':
        if coords == 'GLOBAL':
            [verts.append((world @ v.co).to_tuple())for v in bm.verts]
        elif coords == 'LOCAL':
            [verts.append(v.co.to_tuple())for v in bm.verts]
    
        [to_select.append(in_bbox(lbound, ubound, v))for v in verts]
        
        for vert_obj, select in zip(bm.verts, to_select):
            if additive:
                vert_obj.select |= select
            else:
                vert_obj.select = select
    
    if select_mode == 'EDGE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in e.verts]) for e in bm.edges]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in e.verts]) for e in bm.edges]
            
        [to_select.append(all(in_bbox(lbound, ubound, v)for v in e)) for e in verts]
        
        for edge_obj, select in zip(bm.edges, to_select):
            if additive:
                edge_obj.select |= select
            else:
                edge_obj.select = select
            
    if select_mode == 'FACE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in f.verts])for f in bm.faces]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in f.verts]) for f in bm.faces]
        
        [to_select.append(all(in_bbox(lbound, ubound, v) for v in f))for f in verts]
        
        for face_obj, select in zip(bm.faces, to_select):
            if additive:
                face_obj.select |= select
            else:
                face_obj.select = select
                
    #update the edit mesh so we get live highlighting
    bmesh.update_edit_mesh(bpy.context.object.data)

    return sum([1 for s in to_select if s])