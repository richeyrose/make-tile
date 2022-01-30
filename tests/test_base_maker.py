import pytest
import bpy

def test_MT_OT_Make_Mini_Base(fake_context):
    scene = fake_context.get('scene')
    scene_props = scene.mt_scene_props
    scene_props.tile_type = 'MINI_BASE'
    op = bpy.ops.object.make_mini_base(
        fake_context,
        refresh=True,
        base_blueprint='ROUND'
    )
    assert op == {'FINISHED'}

