import pytest
import bpy

def test_MT_OT_Convert_To_MT_Obj(cube):
    assert bpy.ops.object.convert_to_make_tile() == {'FINISHED'}