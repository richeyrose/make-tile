import pytest
import bpy

@pytest.mark.parametrize("main_part_blueprint, base_blueprint, operator_return",
                         [('OPENLOCK', 'OPENLOCK', {'FINISHED'}),
                          ('OPENLOCK', 'PLAIN', {'FINISHED'}),
                          ('OPENLOCK', 'NONE', {'FINISHED'}),
                          ('OPENLOCK', 'OPENLOCK_S_WALL', {'FINISHED'}),
                          ('OPENLOCK', 'PLAIN_S_WALL', {'FINISHED'}),
                          ('PLAIN', 'PLAIN', {'FINISHED'}),
                          ('PLAIN', 'OPENLOCK', {'FINISHED'}),
                          ('PLAIN', 'NONE', {'FINISHED'}),
                          ('NONE', 'NONE', {'FINISHED'})])
def test_MT_OT_Make_L_Wall_Tile_types(fake_context, main_part_blueprint, base_blueprint, operator_return):
    scene = fake_context.get('scene')
    scene_props = scene.mt_scene_props
    scene_props.tile_type = "L_WALL"
    op = bpy.ops.object.make_l_wall_tile(
        fake_context,
        refresh=True,
        main_part_blueprint = main_part_blueprint,
        base_blueprint = base_blueprint)
    assert op == operator_return