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

#todo ensure these work in obejct mode as well as mesh mode
def select_all():
    current_mode = bpy.context.object.mode
    if current_mode == 'EDIT':
        bpy.ops.mesh.select_all(action="SELECT")
        return {'FINSIHED'}
    elif current_mode == 'OBJECT':
        bpy.ops.object.select_all(action="SELECT")
        return {'FINISHED'}
    else:
        return {'FINSIHED'}

def deselect_all():
    current_mode = bpy.context.object.mode
    if current_mode == 'EDIT':
        bpy.ops.mesh.select_all(action="DESELECT")
        return {'FINSIHED'}
    elif current_mode == 'OBJECT':
        bpy.ops.object.select_all(action="DESELECT")
        return {'FINISHED'}
    else:
        return {'FINSIHED'}