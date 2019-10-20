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
    "name" : "Make Tile",
    "author" : "Richard Rose",
    "description" : "Add on for creating 3d printable tiles",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D > UI > Make-Tile",
    "warning" : "",
    "category" : "3D View"
}

import bpy
import os
from . ui.panels import MT_PT_Panel
from . operators.maketile import MT_OT_makeTile
from . operators.makevertgroups import MT_OT_makeVertGroupsFromFaces
from . preferences import MT_makeTilePreferences
from . utils.registration import get_path_name, get_path

#Begin debug block

#TODO: delete below debug messages
print("get_path: " + get_path())
print("get_path_name: " + get_path_name())

#End debug block


classes = (MT_OT_makeTile, MT_PT_Panel, MT_OT_makeVertGroupsFromFaces, MT_makeTilePreferences)

register, unregister = bpy.utils.register_classes_factory(classes)