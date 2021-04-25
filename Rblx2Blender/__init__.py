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
    "name" : "Rblx To Blender",
    "author" : "mallgrab",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Object"
}

import bpy

from . rblx_pnl import RBLX_PT_Panel
from . rblx_pnl import RBLX_Place_Path
from . rblx_pnl import RBLX_Install_Path
from . rblx_pnl import StartConverting
from . rblx_pnl import TestCheckBox

classes = (RBLX_PT_Panel, RBLX_Place_Path, RBLX_Install_Path, StartConverting, TestCheckBox)

def register():
    for i in classes:
        bpy.utils.register_class(i)

    bpy.types.Scene.Place_Path = bpy.props.PointerProperty(type=RBLX_Place_Path)
    bpy.types.Scene.Install_Path = bpy.props.PointerProperty(type=RBLX_Install_Path)
    bpy.types.Scene.Test_Boolean = bpy.props.PointerProperty(type=TestCheckBox)

def unregister():
    for i in classes:
        bpy.utils.unregister_class(i)
