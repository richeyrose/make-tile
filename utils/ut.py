import bpy

#select object by name
def select(objName):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[objName].select_set(True)

#activate object by name    
def activate(objName):
    bpy.context.view_layer.objects.active = bpy.data.objects[objName]

#Delete an object by name
def delete(objName):
    select(objName)
    bpy.ops.object.delete(use_global=False)
    
#Delete all objects
def delete_all():
    if(len(bpy.data.objects)!=0):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
#switch modes cleanly
def mode(mode_name):
    if(len(bpy.data.objects)!=0):
        bpy.ops.object.mode_set(mode=mode_name)
        if mode_name == "EDIT":
            bpy.ops.mesh.select_all(action="DESELECT")

def select_all():
    bpy.ops.mesh.select_all(action="SELECT")

def deselect_all():
    bpy.ops.mesh.select_all(action="DESELECT")