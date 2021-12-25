import pytest
import bpy

@pytest.mark.parametrize("main_part_blueprint, base_blueprint, operator_return",
                         [('OPENLOCK', 'OPENLOCK', {'FINISHED'}),
                          ('OPENLOCK', 'PLAIN', {'FINISHED'}),
                          ('OPENLOCK', 'OPENLOCK_S_WALL', {'FINISHED'}),
                          ('OPENLOCK', 'PLAIN_S_WALL', {'FINISHED'}),
                          ('OPENLOCK', 'NONE', {'FINISHED'}),
                          ('PLAIN', 'PLAIN', {'FINISHED'}),
                          ('PLAIN', 'OPENLOCK', {'FINISHED'}),
                          ('PLAIN', 'NONE', {'FINISHED'}),
                          ('NONE', 'NONE', {'FINISHED'})])
def test_Make_Straight_Wall_OT_types(fake_context, main_part_blueprint, base_blueprint, operator_return):
    scene = fake_context.get('scene')
    scene_props = scene.mt_scene_props
    scene_props.tile_type = "STRAIGHT_WALL"
    op = bpy.ops.object.make_straight_wall(
        fake_context,
        refresh=True,
        main_part_blueprint = main_part_blueprint,
        base_blueprint = base_blueprint)
    assert op == operator_return

@pytest.mark.parametrize("wall_position, operator_return",
                         [("CENTER", {'FINISHED'}),
                          ("SIDE", {'FINISHED'}),
                          ("EXTERIOR", {'FINISHED'})])
def test_Make_Straight_Wall_OT_wall_position(fake_context, wall_position, operator_return):
    scene = fake_context.get('scene')
    scene_props = scene.mt_scene_props
    scene_props.tile_type = "STRAIGHT_WALL"
    op = bpy.ops.object.make_straight_wall(
        fake_context,
        refresh=True,
        main_part_blueprint='PLAIN',
        base_blueprint='PLAIN_S_WALL',
        wall_position=wall_position)
    assert op == operator_return

