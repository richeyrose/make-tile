import bpy
import bmesh
import mathutils

def scene_bounding_box():
    # Get names of all meshes in scene
    mesh_names = [v.name for v in bpy.context.scene.objects if v.type == 'MESH']
    # Save an initial value
    # Save as list for single-entry modification
    co = coords(mesh_names[0])[0]
    bb_max = [co[0], co[1], co[2]]
    bb_min = [co[0], co[1], co[2]]
    # Test and store maxima and mimima
    for i in range(0, len(mesh_names)):
        co = coords(mesh_names[i])
        for j in range(0, len(co)):
            for k in range(0, 3):
                if co[j][k] > bb_max[k]:
                    bb_max[k] = co[j][k]
                if co[j][k] < bb_min[k]:
                    bb_min[k] = co[j][k]
    # Convert to tuples
    bb_max = (bb_max[0], bb_max[1], bb_max[2])
    bb_min = (bb_min[0], bb_min[1], bb_min[2])
    return [bb_min, bb_max]

#lbound = lowest left of cuboid
#ubound = upper right of cuboid
def in_bbox(lbound, ubound, v, buffer=0.0001):
    return lbound[0]-buffer <=v[0]<=ubound[0]+buffer and \
    lbound[1]-buffer<=v[1]<=ubound[1]+buffer and \
    lbound[2]-buffer<=v[2]<=ubound[2]+buffer

def select_by_loc(lbound=(0,0,0), ubound=(0,0,0), 
    select_mode='VERT', coords='GLOBAL', additive = True):
    #set selection mode
    bpy.ops.mesh.select_mode(type=select_mode)
    #grab the transformation matrix
    world = bpy.context.object.matrix_world
    
    #instantiate a bmesh object and ensure lookup table (bm.faces.ensure... works for all)
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    bm.faces.ensure_lookup_table()
    
    #initialise list of verts and parts to be selected
    verts=[]
    to_select=[]
    
    #for VERT, EDGE or FACE
        #grab list of global or local coords
        #test if the piece is entirely within the rectangular
        #prism defined by lbound and ubound
        #select each piece that returned TRUE and deselect each piece that returned FALSE
        
    if select_mode=='VERT':
        if coords =='GLOBAL':
            [verts.append((world @ v.co).to_tuple())for v in bm.verts]
        elif coords == 'LOCAL':
            [verts.append(v.co.to_tuple())for v in bm.verts]
    
        [to_select.append(in_bbox(lbound, ubound, v))for v in verts]
        
        for vertObj, select in zip(bm.verts, to_select):
            if additive:
                vertObj.select |= select
            else:
                vertObj.select = select
    
    if select_mode == 'EDGE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in e.verts]) for e in bm.edges]
        elif coords=='LOCAL':
            [verts.append([v.co.to_tuple()for v in e.verts]) for e in bm.edges]
            
        [to_select.append(all(in_bbox(lbound, ubound, v)for v in e)) for e in verts]
        
        for edgeObj, select in zip(bm.edges, to_select):
            if additive:
                edgeObj.select |= select
            else:
                edgeObj.select = select
            
    if select_mode == 'FACE':
        if coords == 'GLOBAL':
            [verts.append([(world @ v.co).to_tuple() for v in f.verts])for f in bm.faces]
        elif coords == 'LOCAL':
            [verts.append([v.co.to_tuple()for v in f.verts]) for f in bm.faces]
        
        [to_select.append(all(in_bbox(lbound, ubound, v) for v in f))for f in verts]
        
        for faceObj, select in zip(bm.faces,to_select):
            if additive:
                faceObj.select |= select
            else:
                faceObj.select = select
                
    #update the edit mesh so we get live highlighting             
    bmesh.update_edit_mesh(bpy.context.object.data)

    return sum([1 for s in to_select if s])