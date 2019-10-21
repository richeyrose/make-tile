"""Contains useful methods for selecting and deleting objects and mode switching"""

import bpy

#select object by name
def select(obj_name):
    """select object by name"""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[obj_name].select_set(True)

def activate(obj_name):
    """activate object by name """
    bpy.context.view_layer.objects.active = bpy.data.objects[obj_name]

def delete_object(obj_name):
    """Delete an object by name"""
    select(obj_name)
    bpy.ops.object.delete(use_global=False)

def delete_all():
    """delete all objects or verts / edges /faces"""
    current_mode = bpy.context.object.mode
    if current_mode == 'OBJECT':
        if len(bpy.data.objects) != 0:
            select_all()
            bpy.ops.object.delete(use_global=False)
    if current_mode == 'EDIT':
        select_all()
        bpy.ops.mesh.delete()

def mode(mode_name):
    """switch modes, ensuring that if we enter edit mode we deselect all selected vertices"""
    if len(bpy.data.objects) != 0:
        bpy.ops.object.mode_set(mode=mode_name)
        if mode_name == "EDIT":
            bpy.ops.mesh.select_all(action="DESELECT")

def select_all():
    """Selects all objects if in OBJECT mode or verts / edges / faces if in EDIT mode"""
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
    """Deselects all objects if in OBJECT mode or verts / edges / faces if in EDIT mode"""
    current_mode = bpy.context.object.mode
    if current_mode == 'EDIT':
        bpy.ops.mesh.select_all(action="DESELECT")
        return {'FINSIHED'}
    if current_mode == 'OBJECT':
        bpy.ops.object.select_all(action="DESELECT")
        return {'FINISHED'}

    return {'FINSIHED'}
