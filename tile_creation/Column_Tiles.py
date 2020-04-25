import bpy
from .. utils.registration import get_prefs
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.selection import select, deselect_all, activate
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials,
    add_preview_mesh_subsurf)
from .create_tile import MT_Tile


class MT_Column_Tile(MT_Tile):
    def __init__(self, tile_props):
        MT_Tile.__init__(self, tile_props)

    def create_plain_base(self, tile_props):
        return super().create_plain_base(tile_props)

    def create_openlock_base(self, tile_props):
        return super().create_openlock_base(tile_props)

    def create_empty_base(self, tile_props):
        return super().create_empty_base(tile_props)

    def create_plain_cores(self, base, tile_props):
        return super().create_plain_cores(base, tile_props)

    def create_openlock_cores(self, base, tile_props):
        return super().create_openlock_cores(base, tile_props)

    def create_core(self, tile_props):
        return super().create_core(tile_props)

    def create_cores(self, base, tile_props, textured_vertex_groups):
        return super().create_cores(base, tile_props, textured_vertex_groups)

    def finalise_tile(self, base, preview_core, cursor_orig_loc, cursor_orig_rot):
        return super().finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot)

