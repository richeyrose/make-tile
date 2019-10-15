import bpy

def scale(objName, v):
    bpy.data.objects[objName].scale = v
    
def location(objName, v):
    bpy.data.objects[objName].location = v
    
def rotation(objName, v):
    bpy.data.objects[objName].rotation_euler = v