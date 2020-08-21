import os
import bpy
from .. utils.registration import get_prefs
from . create_displacement_mesh import create_displacement_object
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group
from .. lib.utils.collections import add_object_to_collection
from .. lib.utils.selection import select, deselect_all, activate
from .. materials.materials import (
    assign_displacement_materials,
    assign_preview_materials,
    add_preview_mesh_subsurf)


def create_displacement_core(base, preview_core, tile_props, textured_vertex_groups):
    """Return the preview and displacement cores."""
    scene = bpy.context.scene
    preferences = get_prefs()

    # For some reason iterating doesn't work here so lock these individually so user
    # can only transform base
    preview_core.lock_location[0] = True
    preview_core.lock_location[1] = True
    preview_core.lock_location[2] = True
    preview_core.lock_rotation[0] = True
    preview_core.lock_rotation[1] = True
    preview_core.lock_rotation[2] = True
    preview_core.lock_scale[0] = True
    preview_core.lock_scale[1] = True
    preview_core.lock_scale[2] = True

    preview_core.parent = base

    preview_core, displacement_core = create_displacement_object(preview_core)

    primary_material = bpy.data.materials[scene.mt_scene_props.tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    image_size = bpy.context.scene.mt_scene_props.tile_resolution

    # create a vertex group for the displacement modifier
    mod_vert_group_name = construct_displacement_mod_vert_group(displacement_core, textured_vertex_groups)

    assign_displacement_materials(
        displacement_core,
        [image_size, image_size],
        primary_material,
        secondary_material,
        vert_group=mod_vert_group_name)

    assign_preview_materials(
        preview_core,
        primary_material,
        secondary_material,
        textured_vertex_groups)

    preview_core.mt_object_props.geometry_type = 'PREVIEW'
    displacement_core.mt_object_props.geometry_type = 'DISPLACEMENT'

    return preview_core, displacement_core


def finalise_tile(base, preview_core, cursor_orig_loc, cursor_orig_rot):
    # Assign secondary material to our base if its a mesh
    if base.type == 'MESH':
        prefs = get_prefs()
        base.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # Add subsurf modifier to our cores
    if preview_core is not None:
        add_preview_mesh_subsurf(preview_core)

    # Reset location
    base.location = cursor_orig_loc
    cursor = bpy.context.scene.cursor
    cursor.location = cursor_orig_loc
    cursor.rotation_euler = cursor_orig_rot

    deselect_all()
    select(base.name)
    activate(base.name)


def spawn_empty_base(tile_props):
    """Spawn an empty base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: Empty
    """
    tile_props.base_size = (0, 0, 0)
    tile_name = tile_props.tile_name

    base = bpy.data.objects.new(tile_props.tile_name + '.base', None)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_props.tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    base.show_in_front = True

    bpy.context.view_layer.objects.active = base
    return base


def spawn_prefab(context, subclasses, blueprint, mt_type):
    """Spawn a maketile prefab such as a base or tile core(s).

    Args:
        context (bpy.context): Blender context
        subclasses (list): list of all subclasses of MT_Tile_Generator
        blueprint (str): mt_blueprint enum item
        type (str): mt_type enum item

    Returns:
        bpy.types.Object: Prefab
    """
    # ensure we can only run bpy.ops in our eval statements
    allowed_names = {k: v for k, v in bpy.__dict__.items() if k == 'ops'}
    for subclass in subclasses:
        if hasattr(subclass, 'mt_type') and hasattr(subclass, 'mt_blueprint'):
            if subclass.mt_type == mt_type and subclass.mt_blueprint == blueprint:
                eval_str = 'ops.' + subclass.bl_idname + '()'
                eval(eval_str, {"__builtins__": {}}, allowed_names)

    prefab = context.active_object
    return prefab


def load_openlock_top_peg(tile_props):
    """Load an openlock style top peg for stacking wall tiles.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: peg
    """
    prefs = get_prefs()
    tile_name = tile_props.tile_name

    booleans_path = os.path.join(
        prefs.assets_path,
        "meshes",
        "booleans",
        "openlock.blend")

    # load peg bool
    with bpy.data.libraries.load(booleans_path) as (data_from, data_to):
        data_to.objects = ['openlock.top_peg']

    peg = data_to.objects[0]
    peg.name = 'Top Peg.' + tile_name
    add_object_to_collection(peg, tile_name)

    return peg


def set_bool_obj_props(bool_obj, parent_obj, tile_props):
    """Set properties for boolean object used for e.g. clip cutters

    Args:
        bool_obj (bpy.types.Object): Boolean Object
        parent_obj (bpy.types.Object): Object to parent boolean object to
        MakeTile.properties.MT_Tile_Properties: tile properties
    """
    bool_obj.parent = parent_obj
    bool_obj.display_type = 'BOUNDS'
    bool_obj.hide_viewport = True
    bool_obj.hide_render = True

    bool_obj.mt_object_props.is_mt_object = True
    bool_obj.mt_object_props.geometry_type = 'CUTTER'
    bool_obj.mt_object_props.tile_name = tile_props.tile_name


def set_bool_props(bool_obj, target_obj, bool_type):
    """Set Properties for boolean and add bool to target_object's cutters collection.
    This allows boolean to be toggled on and off in MakeTile menu

    Args:
        bool_obj (bpy.types.Object): boolean object
        target_obj (bpy.types.Object): target object
        bool_type (enum): enum in {'DIFFERENCE', 'UNION', 'INTERSECT'}
    """
    boolean = target_obj.modifiers.new(bool_obj.name + '.bool', 'BOOLEAN')
    boolean.operation = bool_type
    boolean.object = bool_obj
    boolean.show_render = False

    # add cutters to object's cutters_collection
    # so we can activate and deactivate them when necessary
    cutter_coll_item = target_obj.mt_object_props.cutters_collection.add()
    cutter_coll_item.name = bool_obj.name
    cutter_coll_item.value = True
    cutter_coll_item.parent = target_obj.name
