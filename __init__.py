# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import bpy
from . preferences import MT_MakeTilePreferences

from . ui.object_generation_panels import (
    MT_PT_Converter_Panel,
    MT_PT_Tile_Generator_Panel)

from . ui.material_panels import (
    MT_PT_Material_Mapping_Options_Panel,
    MT_PT_Material_Options_Panel,
    MT_PT_Material_Slots_Panel,
    MT_PT_Vertex_Groups_Panel)

from . ui.export_panels import (
    MT_PT_Export_Panel,
    MT_PT_Trim_Panel,
    MT_PT_Voxelise_Panel)

from . ui.options_panels import (
    MT_PT_Display_Panel)

# Include tinycad operators as library in case user doesn't have it installed
from . lib.utils.tinycad.BIX import MT_OT_LineOnBisection
from . lib.utils.tinycad.CCEN import MT_OT_CallBackCCEN, MT_OT_CircleCenter
from . lib.utils.tinycad.E2F import MT_OT_EdgeToFace
from . lib.utils.tinycad.V2X import MT_OT_Vert2Intersection
from . lib.utils.tinycad.VTX import MT_OT_AutoVTX
from . lib.utils.tinycad.XALL import MT_OT_IntersectAllEdges

from . operators.maketile import (
    MT_OT_Make_Tile,
    MT_Cutter_Item,
    MT_Trimmer_Item,
    MT_Disp_Mat_Item,
    MT_Tile_Properties,
    MT_Object_Properties,
    MT_Radio_Buttons)

from . operators.copy_material import MT_OT_Copy_Material
from . operators.save_material import MT_OT_Export_Material

from . operators.makevertgroups import MT_OT_makeVertGroupsFromFaces
from . operators.object_converter import MT_OT_Convert_To_MT_Obj
from . operators.bakedisplacement import MT_OT_Bake_Displacement, MT_OT_Assign_Material_To_Vert_Group, MT_OT_Remove_Material_From_Vert_Group
from . operators.return_to_preview import MT_OT_Return_To_Preview
from . operators.create_lighting_setup import MT_OT_Create_Lighting_Setup
from . operators.exporter import MT_OT_Export_Tile
from . operators.voxeliser import MT_OT_Tile_Voxeliser
from . operators.trim_tile import MT_OT_Add_Trimmers
from . lib.turtle.operators.basic_commands import *
from . lib.turtle.operators.curve import *
from . lib.turtle.operators.helpers import *
from . lib.turtle.operators.path import *
from . lib.turtle.operators.selection import *
from . lib.turtle.operators.vertex_group import *
from . lib.turtle.operators.aliases import *


bl_info = {
    "name": "MakeTile",
    "author": "Richard Rose",
    "description": "Add on for creating 3d printable tiles",
    "blender": (2, 80, 1),
    "version": (0, 0, 5),
    "location": "View3D > UI > MakeTile",
    "warning": "",
    "category": "3D View"
}


classes = (
    MT_MakeTilePreferences,
    MT_OT_Copy_Material,
    MT_Radio_Buttons,
    MT_Cutter_Item,
    MT_Trimmer_Item,
    MT_Disp_Mat_Item,
    MT_Tile_Properties,
    MT_Object_Properties,
    MT_OT_Make_Tile,
    MT_OT_Export_Material,
    MT_OT_makeVertGroupsFromFaces,
    MT_OT_Add_Trimmers,
    MT_OT_Convert_To_MT_Obj,
    MT_OT_Bake_Displacement,
    MT_OT_Return_To_Preview,
    MT_OT_Create_Lighting_Setup,
    MT_OT_Tile_Voxeliser,
    MT_OT_Export_Tile,
    MT_OT_Assign_Material_To_Vert_Group,
    MT_OT_Remove_Material_From_Vert_Group,
    MT_OT_LineOnBisection,
    MT_OT_CallBackCCEN,
    MT_OT_CircleCenter,
    MT_OT_EdgeToFace,
    MT_OT_Vert2Intersection,
    MT_OT_AutoVTX,
    MT_OT_IntersectAllEdges,
    MT_PT_Tile_Generator_Panel,
    MT_PT_Display_Panel,
    MT_PT_Material_Slots_Panel,
    MT_PT_Vertex_Groups_Panel,
    MT_PT_Material_Options_Panel,
    MT_PT_Material_Mapping_Options_Panel,
    MT_PT_Voxelise_Panel,
    MT_PT_Trim_Panel,
    MT_PT_Converter_Panel,
    MT_PT_Export_Panel,
    TURTLE_OT_add_turtle,
    TURTLE_OT_clear_screen,
    TURTLE_OT_clean,
    TURTLE_OT_home,
    TURTLE_OT_pen_down,
    TURTLE_OT_pen_up,
    TURTLE_OT_forward,
    TURTLE_OT_backward,
    TURTLE_OT_up,
    TURTLE_OT_down,
    TURTLE_OT_left,
    TURTLE_OT_right,
    TURTLE_OT_arc,
    TURTLE_OT_left_turn,
    TURTLE_OT_right_turn,
    TURTLE_OT_look_up,
    TURTLE_OT_look_down,
    TURTLE_OT_roll_left,
    TURTLE_OT_roll_right,
    TURTLE_OT_set_pos,
    TURTLE_OT_set_rotation,
    TURTLE_OT_set_heading,
    TURTLE_OT_set_pitch,
    TURTLE_OT_set_roll,
    TURTLE_OT_quadratic_curve,
    TURTLE_OT_cubic_curve,
    TURTLE_OT_begin_path,
    TURTLE_OT_stroke_path,
    TURTLE_OT_fill_path,
    TURTLE_OT_select_all,
    TURTLE_OT_deselect_all,
    TURTLE_OT_select_path,
    TURTLE_OT_new_vert_group,
    TURTLE_OT_select_vert_group,
    TURTLE_OT_deselect_vert_group,
    TURTLE_OT_add_to_vert_group,
    TURTLE_OT_remove_from_vert_group,
    TURTLE_OT_bridge,
    TURTLE_OT_merge,
    TURTLE_OT_select_by_location,
    TURTLE_OT_add_vert,
    TURTLE_OT_select_at_cursor,
    TURTLE_OT_clear_screen_alias,
    TURTLE_OT_pen_down_alias,
    TURTLE_OT_pen_up_alias,
    TURTLE_OT_forward_alias,
    TURTLE_OT_backward_alias,
    TURTLE_OT_down_alias,
    TURTLE_OT_left_alias,
    TURTLE_OT_right_alias,
    TURTLE_OT_left_turn_alias,
    TURTLE_OT_right_turn_alias,
    TURTLE_OT_look_up_alias,
    TURTLE_OT_look_down_alias,
    TURTLE_OT_roll_left_alias,
    TURTLE_OT_roll_right_alias,
    TURTLE_OT_set_pos_alias,
    TURTLE_OT_set_rotation_alias,
    TURTLE_OT_set_heading_alias,
    TURTLE_OT_set_roll_alias,
    TURTLE_OT_quadratic_curve_alias,
    TURTLE_OT_cubic_curve_alias,
    TURTLE_OT_select_all_alias,
    TURTLE_OT_deselect_all_alias,
    TURTLE_OT_select_path_alias,
    TURTLE_OT_new_vert_group_alias,
    TURTLE_OT_select_vert_group_alias,
    TURTLE_OT_deselect_vert_group_alias,
    TURTLE_OT_add_to_vert_group_alias,
    TURTLE_OT_remove_from_vert_group_alias)

register, unregister = bpy.utils.register_classes_factory(classes)
