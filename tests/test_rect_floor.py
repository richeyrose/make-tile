import pytest
import bpy
from .test_straight_wall_gen import fake_context

@pytest.mark.parametrize("main_part_blueprint, base_blueprint, operator_return",
                         [('PLAIN', 'PLAIN', {'FINISHED'}),
                          ('PLAIN', 'OPENLOCK', {'FINISHED'}),
                          ('PLAIN', 'NONE', {'FINISHED'}),
                          ('NONE', 'NONE', {'FINISHED'})])
def test_make_Rect_Floor_OT_types(fake_context, main_part_blueprint, base_blueprint, operator_return):
    op = bpy.ops.object.make_rect_floor(
        fake_context,
        refresh=True,
        main_part_blueprint = main_part_blueprint,
        base_blueprint = base_blueprint)

    assert op == operator_return

