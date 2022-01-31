import pytest
import bpy


@pytest.mark.parametrize("blueprint, operator_return",
                         [('OVAL', {'FINISHED'}),
                          ('ROUND', {'FINISHED'}),
                          ('POLY', {'FINISHED'}),
                          ('RECT', {'FINISHED'}),
                          ('ROUNDED_RECT', {'FINISHED'})])
def test_MT_OT_Make_Mini_Base(blueprint, operator_return):
    scene = bpy.context.scene
    scene_props = scene.mt_scene_props
    scene_props.tile_type = "MINI_BASE"
    scene_props.base_blueprint = blueprint
    op = bpy.ops.object.make_mini_base(base_blueprint=blueprint, refresh=True)
    assert op == operator_return
