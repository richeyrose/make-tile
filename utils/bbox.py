import bpy

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