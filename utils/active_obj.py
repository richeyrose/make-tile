import bpy
import bmesh
import mathutils
from . bbox import in_bbox

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

            

def location(v):
    bpy.context.object.location = v
        
def scale(v):
    bpy.context.object.scale = v
    
def rotation(v):
    bpy.context.object.rotation_euler = v
    
def rename(objName):
    bpy.context.object.name = objName
    
def register_bmesh():
    return bmesh.from_edit_mesh(bpy.context.object.data)
    
def select_vert(bm, i):
    bm.verts.ensure_lookup_table()
    bm.verts[i].select = True

def select_edge(bm, e):
    bm.edges.ensure_lookup_table()
    bm.edges[e].select = True
    
def select_face(bm, f):
    bm.faces.ensure_lookup_table()
    bm.faces[f].select = True
    
def deselect_all():
    bpy.ops.mesh.select_all(action="DESELECT")

def extrude(v):
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate = 
            {"value":v,
            "constraint_axis": (True, True, True),
            "constraint_orientation":'NORMAL'})
            
def subdivide(cuts = 1):
    bpy.ops.mesh.subdivide(number_cuts = cuts)
    
def randomize(intensity = 0.1):
    bpy.ops.transform.vertex_random(offset = intensity)

   