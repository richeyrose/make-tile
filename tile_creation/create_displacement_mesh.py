""" Contains functions for turning objects into displacement meshes"""


def create_displacement_object(obj):
    '''Takes a mesh object and returns a displacement and preview object'''

    # add subsurf modifier
    subsurf = obj.modifiers.new('Subsurf', 'SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 3
    obj['subsurf_mod_name'] = subsurf.name

    # add a geometry_type custom property so MakeTile knows that these objects
    # are preview / displacement objects
    obj.mt_object_props.geometry_type = 'PREVIEW'

    return obj
