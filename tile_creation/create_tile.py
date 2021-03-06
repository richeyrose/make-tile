import os
import bpy
from ..operators.assign_reference_object import assign_obj_to_obj_texture_coords
from .. utils.registration import get_prefs
from .. lib.utils.vertex_groups import construct_displacement_mod_vert_group
from .. lib.utils.collections import add_object_to_collection, create_collection
from .. lib.utils.selection import select, deselect_all, activate
from .. materials.materials import (
    assign_mat_to_vert_group)
from ..operators.assign_reference_object import create_helper_object

class MT_Tile_Generator:
    """Subclass this to create your tile operator."""

    @classmethod
    def poll(cls, context):
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True


def initialise_tile_creator(context):
    deselect_all()
    scene = context.scene
    scene_props = scene.mt_scene_props

    # Root collection to which we add all tiles
    tiles_collection = create_collection('Tiles', scene.collection)

    # create helper object for material mapping
    create_helper_object(context)

    # set tile name
    tile_name = scene_props.tile_type.lower()

    # We create tile at origin and then move it to original location
    # this stops us from having to update the view layer every time
    # we parent an object
    cursor = scene.cursor
    cursor_orig_loc = cursor.location.copy()
    cursor_orig_rot = cursor.rotation_euler.copy()
    cursor.location = (0, 0, 0)
    cursor.rotation_euler = (0, 0, 0)

    return tile_name, tiles_collection, cursor_orig_loc, cursor_orig_rot


def create_common_tile_props(scene_props, tile_props, tile_collection):
    """Create properties common to all tiles."""
    tile_props.tile_name = tile_collection.name
    tile_props.is_mt_collection = True
    tile_props.tile_blueprint = scene_props.tile_blueprint
    tile_props.main_part_blueprint = scene_props.main_part_blueprint
    tile_props.base_blueprint = scene_props.base_blueprint
    tile_props.UV_island_margin = scene_props.UV_island_margin
    tile_props.tile_units = scene_props.tile_units
    tile_props.tile_resolution = scene_props.tile_resolution
    tile_props.texture_margin = scene_props.texture_margin
    tile_props.collection_type = "TILE"

def lock_all_transforms(obj):
    """Lock all transforms.

    Args:
        obj (bpy.type.Object): object
    """
    # For some reason iterating doesn't work here
    obj.lock_location[0] = True
    obj.lock_location[1] = True
    obj.lock_location[2] = True
    obj.lock_rotation[0] = True
    obj.lock_rotation[1] = True
    obj.lock_rotation[2] = True
    obj.lock_scale[0] = True
    obj.lock_scale[1] = True
    obj.lock_scale[2] = True


def convert_to_displacement_core(core, textured_vertex_groups):
    """Convert the core part of an object so it can be used by the MakeTile dispacement system.

    Args:
        core (bpy.types.Object): object to convert
        textured_vertex_groups (list[str]): list of vertex group names that should have a texture applied
    """
    scene = bpy.context.scene
    preferences = get_prefs()
    props = core.mt_object_props
    scene_props = scene.mt_scene_props
    primary_material = bpy.data.materials[scene_props.tile_material_1]
    secondary_material = bpy.data.materials[preferences.secondary_material]

    # create new displacement modifier
    disp_mod = core.modifiers.new('MT Displacement', 'DISPLACE')
    disp_mod.strength = 0
    disp_mod.texture_coords = 'UV'
    disp_mod.direction = 'NORMAL'
    disp_mod.mid_level = 0
    disp_mod.show_render = True

    # save modifier name as custom property for use my maketile
    props.disp_mod_name = disp_mod.name
    props.displacement_strength = scene_props.displacement_strength
    # core['disp_mod_name'] = disp_mod.name

    # create a vertex group for the displacement modifier
    vert_group = construct_displacement_mod_vert_group(core, textured_vertex_groups)
    disp_mod.vertex_group = vert_group

    # create texture for displacement modifier
    props.disp_texture = bpy.data.textures.new(core.name + '.texture', 'IMAGE')
    '''
    # add a triangulate modifier to correct for distortion after bools
    core.modifiers.new('MT Triangulate', 'TRIANGULATE')
    '''
    # add a subsurf modifier
    subsurf = core.modifiers.new('MT Subsurf', 'SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    props.subsurf_mod_name = subsurf.name
    core.cycles.use_adaptive_subdivision = True

    # move subsurf modifier to top of stack
    ctx = {
        'object': core,
        'active_object': core,
        'selected_objects': [core],
        'selected_editable_objects': [core]
    }

    bpy.ops.object.modifier_move_to_index(ctx, modifier=subsurf.name, index=0)

    subsurf.levels = 3

    # switch off subsurf modifier if we are not in cycles mode
    if bpy.context.scene.render.engine != 'CYCLES':
        subsurf.show_viewport = False

    # assign materials
    if secondary_material.name not in core.data.materials:
        core.data.materials.append(secondary_material)

    if primary_material.name not in core.data.materials:
        core.data.materials.append(primary_material)

    for group in textured_vertex_groups:
        assign_mat_to_vert_group(group, core, primary_material)

    # flag core as a displacement object
    core.mt_object_props.is_displacement = True
    core.mt_object_props.geometry_type = 'CORE'


def finalise_core(core, tile_props):
    """Finalise core.

    Set origin, UV project, set object props

    Args:
        core (bpy.types.Object): core
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties
    """
    ctx = {
        'object': core,
        'active_object': core,
        'selected_editable_objects': [core],
        'selected_objects': [core]
    }

    bpy.ops.object.origin_set(ctx, type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.object.editmode_toggle(ctx)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(ctx, island_margin=tile_props.UV_island_margin)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle(ctx)

    obj_props = core.mt_object_props
    obj_props.is_mt_object = True
    obj_props.tile_name = tile_props.tile_name


def finalise_tile(base, core, cursor_orig_loc, cursor_orig_rot):
    """Finalise tile.

    Parent core to base, assign secondary material to base, reset cursor,
    select and activate base.

    Args:
        base (bpy.type.Object): base
        core (bpy.types.Object): core
        cursor_orig_loc (Vector(3)): original cursor location
        cursor_orig_rot (Vector(3)): original cursor rotation
    """
    context = bpy.context
    # Assign secondary material to our base if its a mesh
    if base.type == 'MESH':
        prefs = get_prefs()
        base.data.materials.append(bpy.data.materials[prefs.secondary_material])

    # Reset location
    base.location = cursor_orig_loc
    cursor = context.scene.cursor
    cursor.location = cursor_orig_loc
    cursor.rotation_euler = cursor_orig_rot

    # Parent core to base
    if core is not None:
        core.parent = base

        # lock all transforms so we can only translate base
        lock_all_transforms(core)

    # deselect any currently selected objects
    for obj in context.selected_objects:
        obj.select_set(False)

    base.select_set(True)
    context.view_layer.objects.active = base


def spawn_empty_base(tile_props):
    """Spawn an empty base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: Empty
    """
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

# TODO: #3 Fix bug where toggling booleans in UI doesn't work if core or base have been renamed
def set_bool_obj_props(bool_obj, parent_obj, tile_props, bool_type):
    """Set properties for boolean object used for e.g. clip cutters.

    Args:
        bool_obj (bpy.types.Object): Boolean Object
        parent_obj (bpy.types.Object): Object to parent boolean object to
        MakeTile.properties.MT_Tile_Properties: tile properties
        bool_type (enum): enum in {'DIFFERENCE', 'UNION', 'INTERSECT'}
    """
    bpy.context.view_layer.update()

    if bool_obj.parent:
        matrix_copy = bool_obj.matrix_world.copy()
        bool_obj.parent = None
        bool_obj.matrix_world = matrix_copy

    bool_obj.parent = parent_obj
    bool_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

    bool_obj.display_type = 'BOUNDS'
    # bool_obj.hide_set(True)
    bool_obj.hide_viewport = True
    bool_obj.hide_render = True

    bool_obj.mt_object_props.is_mt_object = True
    bool_obj.mt_object_props.boolean_type = bool_type
    bool_obj.mt_object_props.tile_name = tile_props.tile_name


def set_bool_props(bool_obj, target_obj, bool_type, solver='FAST'):
    """Set Properties for boolean and add bool to target_object's cutters collection.

    This allows boolean to be toggled on and off in MakeTile menu

    Args:
        bool_obj (bpy.types.Object): boolean object
        target_obj (bpy.types.Object): target object
        bool_type (enum): enum in {'DIFFERENCE', 'UNION', 'INTERSECT'}
        solver (enum in {'FAST', 'EXACT'}): Whether to use new exact solver
    """
    boolean = target_obj.modifiers.new(bool_obj.name + '.bool', 'BOOLEAN')
    boolean.solver = solver
    boolean.operation = bool_type
    boolean.object = bool_obj
    boolean.show_render = True

    # add cutters to object's cutters_collection
    # so we can activate and deactivate them when necessary
    cutter_coll_item = target_obj.mt_object_props.cutters_collection.add()
    cutter_coll_item.name = bool_obj.name
    cutter_coll_item.value = True
    bpy.context.view_layer.update()
    cutter_coll_item.parent = target_obj.name
