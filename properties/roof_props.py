import bpy
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup
from bpy.props import (
    EnumProperty,
    BoolProperty,
    FloatProperty,
    PointerProperty)


class MT_Roof_Properties(PropertyGroup):

    last_selected: PointerProperty(
        name="Last Selected Object",
        type=bpy.types.Object)

    roof_type: EnumProperty(
        name="Roof Type",
        items=[
            ("APEX", "Apex", ""),
            ("NADIR", "Nadir", ""),
            ("SIDE", "Side", "")],
        default="APEX"
    )

    roof_pitch: FloatProperty(
        name="Roof Pitch",
        default=45,
        step=1,
        min=0
    )

    end_eaves_pos: FloatProperty(
        name="End Eaves Positive",
        default=0.1,
        step=0.1,
        min=0
    )

    end_eaves_neg: FloatProperty(
        name="End Eaves Negative",
        default=0.1,
        step=0.1,
        min=0
    )

    side_eaves: FloatProperty(
        name="Side Eaves",
        default=0.2,
        step=0.1,
        min=0
    )

    roof_thickness: FloatProperty(
        name="Roof Thickness",
        default=0.1,
        step=0.05,
        min=0
    )

    draw_rooftop: BoolProperty(
        name="Draw Rooftop?",
        default=True,
        description="Whether to draw the rooftop portion of the roof or just the Eaves."
    )

    draw_gables: BoolProperty(
        name="Draw Gables?",
        default=True,
        description="Whether to draw the Gables."
    )

    inset_dist: FloatProperty(
        name="Inset Distance",
        description="Distance core is usually inset from the base of a wall",
        default=0.09,
        min=0
    )

    inset_x_neg: BoolProperty(
        name="Inset X Neg",
        default=True)

    inset_x_pos: BoolProperty(
        name="Inset X Pos",
        default=True)

    inset_y_neg: BoolProperty(
        name="Inset Y Neg",
        default=True)

    inset_y_pos: BoolProperty(
        name="Inset Y Pos",
        default=True)

    base_bottom_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        name="Base Bottom Socket",
        default='OPENLOCK')

    base_side_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        default='NONE',
        name="Base Side Socket")

    gable_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("NONE", "None", "")],
        default='NONE',
        name="Gable Side Socket")

    is_roof: BoolProperty(
        default=False
    )


@persistent
def update_mt_roof_scene_props_handler(dummy):
    """Check to see if we have a MakeTile roof object selected and updates mt_roof_scene_props based on its mt_roof_tile_props."""

    context = bpy.context
    obj = context.object
    roof_scene_props = context.scene.mt_roof_scene_props

    try:
        roof_tile_props = bpy.data.collections[obj.mt_object_props.tile_name].mt_roof_tile_props

        if obj != roof_scene_props.last_selected and roof_tile_props.is_roof:
            for key, value in roof_tile_props.items():
                for k in roof_scene_props.keys():
                    if k == key:
                        roof_scene_props[k] = value
            roof_scene_props.last_selected = obj

    except KeyError:
        pass
    except AttributeError:
        pass

bpy.app.handlers.depsgraph_update_post.append(update_mt_roof_scene_props_handler)

def register():
    # Property group that contains properties set in UI
    bpy.types.Scene.mt_roof_scene_props = PointerProperty(
        type=MT_Roof_Properties)
    bpy.types.Collection.mt_roof_tile_props = PointerProperty(
        type=MT_Roof_Properties)


def unregister():
    del bpy.types.Collection.mt_roof_tile_props
    del bpy.types.Scene.mt_roof_scene_props