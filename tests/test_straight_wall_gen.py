import pytest
import bpy

@pytest.fixture
def fake_context():
    scene = bpy.data.scenes.new('fake_scene')
    view_layer = view_layer = bpy.data.scenes['fake_scene'].view_layers['ViewLayer']
    return {
        'scene': scene,
        'view_layer': view_layer}


@pytest.mark.parametrize("main_part_blueprint, base_blueprint, operator_return",
                         [('OPENLOCK', 'OPENLOCK', {'FINISHED'}),
                          ('OPENLOCK', 'PLAIN', {'FINISHED'}),
                          ('OPENLOCK', 'NONE', {'FINISHED'}),
                          ('PLAIN', 'PLAIN', {'FINISHED'}),
                          ('PLAIN', 'OPENLOCK', {'FINISHED'}),
                          ('PLAIN', 'NONE', {'FINISHED'}),
                          ('NONE', 'NONE', {'FINISHED'})])

def test_make_Straight_Wall_OT(fake_context, main_part_blueprint, base_blueprint, operator_return):
    op = bpy.ops.object.make_straight_wall(
        fake_context,
        refresh=True,
        main_part_blueprint = main_part_blueprint,
        base_blueprint = base_blueprint)

    assert op == operator_return

