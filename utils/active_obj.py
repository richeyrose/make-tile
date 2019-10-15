import bpy
import bmesh
import mathutils
from . bbox import in_bbox

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
    
def extrude(v):
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate = 
            {"value":v,
            "constraint_axis": (True, True, True),
            "constraint_orientation":'NORMAL'})
            
def subdivide(cuts = 1):
    bpy.ops.mesh.subdivide(number_cuts = cuts)
    
def randomize(intensity = 0.1):
    bpy.ops.transform.vertex_random(offset = intensity)

   