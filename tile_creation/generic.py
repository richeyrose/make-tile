import bpy
from .. utils.registration import get_prefs
from .. materials.materials import add_preview_mesh_subsurf


def finalise_tile(tile_meshes,
                  base,
                  preview_core,
                  cursor_orig_loc):

    # Assign secondary material to our base if its a mesh
    if base.type == 'MESH':
        prefs = get_prefs()
        base.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # Add subsurf modifier to our cores
    if preview_core is not None:
        add_preview_mesh_subsurf(preview_core)

    # Reset location
    base.location = cursor_orig_loc
    cursor = bpy.context.scene.cursor
    cursor.location = cursor_orig_loc
