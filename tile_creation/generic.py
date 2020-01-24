import bpy
from .. utils.registration import get_prefs
from .. materials.materials import add_preview_mesh_subsurf
from .. operators.trim_tile import add_bool_modifier


def finalise_tile(tile_meshes,
                  trimmers,
                  tile_empty,
                  base,
                  preview_core,
                  cursor_orig_loc):
    '''add trimmer bools, parent to base etc.
    '''

    for obj in tile_meshes:
        for trimmer in trimmers:
            add_bool_modifier(obj, trimmer.name)

    # Parent our base to our tile empty
    base.parent = tile_empty

    # Assign secondary material to our base if its a mesh
    if base.type == 'MESH':
        prefs = get_prefs()
        base.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # Add subsurf modifier to our cores
    if preview_core is not None:
        add_preview_mesh_subsurf(preview_core)

    # Reset location
    tile_empty.location = cursor_orig_loc
    cursor = bpy.context.scene.cursor
    cursor.location = cursor_orig_loc
