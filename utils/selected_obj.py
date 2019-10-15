import bpy

def translate(v):
    bpy.ops.transform.translate(value=v, constraint_axis=(True, True, True))

def scale(v):
    bpy.ops.transform.resize(value=v, constraint_axis=(True, True, True))

def rotate(v = 0, axis = 'Z'):
    bpy.ops.transform.rotate(value = v, orient_axis = axis)

def transform_apply():
    bpy.ops.object.transform_apply(location = True, rotation=True, scale=True)