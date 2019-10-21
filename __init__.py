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

bl_info = {
    "name" : "MakeTile",
    "author" : "Richard Rose",
    "description" : "Add on for creating 3d printable tiles",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D > UI > MakeTile",
    "warning" : "",
    "category" : "3D View"
}


import os
import bpy

from . ui.panels import MT_PT_Panel
from . operators.maketile import MT_OT_Make_Tile
from . operators.makevertgroups import MT_OT_makeVertGroupsFromFaces
from . preferences import MT_MakeTilePreferences

classes = ( MT_MakeTilePreferences, MT_OT_Make_Tile, MT_PT_Panel, MT_OT_makeVertGroupsFromFaces)

register, unregister = bpy.utils.register_classes_factory(classes)

