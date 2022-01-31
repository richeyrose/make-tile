import pytest
import bpy


def test_MT_OT_Make_3D(straight_wall):
    core = bpy.data.objects['straight_wall.wall_core']
    ctx = {
        'object': core,
        'selected_objects': [core]}
    op = bpy.ops.scene.mt_make_3d(ctx)
    assert op == {'FINISHED'}
