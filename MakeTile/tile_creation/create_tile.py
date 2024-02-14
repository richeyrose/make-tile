import os
from math import floor
from weakref import KeyedRef
import bpy
from bpy.types import Operator
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty)

from ..operators.assign_reference_object import (
    create_helper_object)

from ..utils.registration import get_prefs

from ..lib.utils.vertex_groups import construct_displacement_mod_vert_group
from ..lib.utils.collections import (
    add_object_to_collection,
    create_collection,
    activate_collection)

from ..lib.utils.selection import deselect_all
from ..lib.utils.multimethod import multimethod
from ..materials.materials import assign_mat_to_vert_group
from ..lib.utils.utils import get_all_subclasses, get_annotations
from ..lib.utils.file_handling import absolute_file_paths

from ..enums.enums import (
    units,
    collection_types)

from ..app_handlers import load_tile_defaults
'''
from line_profiler import LineProfiler
from os.path import splitext
profile = LineProfiler()
'''


def tile_x_update(self, context):
    if self.x_proportionate_scale:
        self.base_x = self.tile_x


def tile_y_update(self, context):
    if self.y_proportionate_scale:
        self.base_y = self.tile_y


def tile_z_update(self, context):
    if self.z_proportionate_scale:
        self.base_z = self.tile_z


def create_tile_type_enums(self, context):
    """Create an enum of tile types out of subclasses of MT_OT_Make_Tile."""
    enum_items = []
    if context is None:
        return enum_items

    # blueprint = context.scene.mt_scene_props.tile_blueprint
    subclasses = get_all_subclasses(MT_Tile_Generator)

    for subclass in subclasses:
        # if hasattr(subclass, 'mt_blueprint'):
        if 'INTERNAL' not in subclass.bl_options:
            enum = (subclass.mt_type, subclass.bl_label, "")
            enum_items.append(enum)
    return sorted(enum_items)


def create_main_part_blueprint_enums(self, context):
    """Dynamically creates a list of enum items depending on what is set in the tile_type defaults.

    Args:
        context (bpy.Context): scene context

    Returns:
        list[enum_item]: list of enum items
    """
    enum_items = []

    if context is None:
        return enum_items

    scene = context.scene
    scene_props = scene.mt_scene_props

    tile_type = scene_props.tile_type
    tile_defaults = load_tile_defaults(context)

    for default in tile_defaults:
        if default['type'] == tile_type:
            try:
                for key, value in default['main_part_blueprints'].items():
                    enum = (key, value, "")
                    enum_items.append(enum)
                return sorted(enum_items)
            # some tiles such as mini bases don't have a main part
            except KeyError:
                pass
    return enum_items


def create_base_blueprint_enums(self, context):
    enum_items = []
    if context is None:
        return enum_items

    scene = context.scene
    scene_props = scene.mt_scene_props

    tile_type = scene_props.tile_type
    tile_defaults = load_tile_defaults(context)

    for default in tile_defaults:
        if default['type'] == tile_type:
            for key, value in default['base_blueprints'].items():
                enum = (key, value, "")
                enum_items.append(enum)
            return sorted(enum_items)
    return enum_items


def update_scene_defaults(self, context):
    if not self.invoked:
        reset_scene_defaults(self, context)


def reset_scene_defaults(self, context):
    scene_props = context.scene.mt_scene_props
    tile_type = scene_props.tile_type
    tile_defaults = load_tile_defaults(context)

    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            for key, value in defaults.items():
                if hasattr(scene_props, key):
                    setattr(scene_props, key, value)
            break
    reset_part_defaults(scene_props, context)


def reset_part_defaults(self, context):
    scene_props = context.scene.mt_scene_props
    tile_type = scene_props.tile_type
    base_blueprint = self.base_blueprint
    main_part_blueprint = self.main_part_blueprint
    floor_material = self.floor_material
    tile_defaults = load_tile_defaults(context)
    for tile in tile_defaults:
        if tile['type'] == tile_type:
            defaults = tile['defaults']
            base_defaults = defaults['base_defaults']
            for key, value in base_defaults.items():
                if key == base_blueprint:
                    for k, v in value.items():
                        setattr(self, k, v)
                    break
            try:
                main_part_defaults = defaults['tile_defaults']
                for key, value in main_part_defaults.items():
                    if key == main_part_blueprint:
                        for k, v in value.items():
                            setattr(self, k, v)
                        break
            # some tiles such as mini bases don't have a main part
            except KeyError:
                pass
            try:
                setattr(self, 'floor_material', defaults['floor_material'])
            except KeyError:
                break
            break


# TODO: Work out why this is called twice by operator
def update_part_defaults(self, context):
    if hasattr(self, 'is_scene_props'):
        reset_part_defaults(self, context)
        return
    else:
        if self.executed:
            reset_part_defaults(self, context)
            return


def create_material_enums(self, context):
    """Return list of default materials as enums.

    Args:
        context (bpy.context): context

    Returns:
        list[EnumPropertyItem]: enum items
    """
    prefs = get_prefs()
    enum_items = []

    if context is None:
        return enum_items

    mats = prefs.default_materials

    for mat in mats:
        enum = (mat.name, mat.name, "")
        enum_items.append(enum)

    return sorted(enum_items)


def create_wall_position_enums(self, context):
    """Return list of wall positions

    Args:
        context (bpy.context): context

    Returns:
        list[EnumPropertyItem]: enum items
    """
    prefs = get_prefs()
    enum_items = []

    if context is None:
        return enum_items

    scene = context.scene
    scene_props = scene.mt_scene_props

    tile_type = scene_props.tile_type
    tile_defaults = load_tile_defaults(context)

    for default in tile_defaults:
        if default['type'] == tile_type:
            try:
                for key, value in default['wall_positions'].items():
                    enum = (key, value, "")
                    enum_items.append(enum)
                return sorted(enum_items)
            except KeyError:
                pass
    return enum_items


class MT_OT_Reset_Tile_Defaults(Operator):
    """Reset mt_scene_props of current tile_type."""

    bl_idname = "scene.reset_tile_defaults"
    bl_label = "Reset Defaults"
    bl_options = {'UNDO'}

    def execute(self, context):
        """Execute the operator.

        Args:
            context (bpy.context): Blender context
        """
        reset_scene_defaults(self, context)

        return {'FINISHED'}


class MT_Tile_Generator:
    """Subclass this to create your tile operator."""

    def create_tile_type_enums(self, context):
        """Create an enum of tile types out of subclasses of MT_OT_Make_Tile."""
        enum_items = []
        if context is None:
            return enum_items
        # blueprint = context.scene.mt_scene_props.tile_blueprint
        subclasses = get_all_subclasses(MT_Tile_Generator)

        for subclass in subclasses:
            # if hasattr(subclass, 'mt_blueprint'):
            if 'INTERNAL' not in subclass.bl_options:
                enum = (subclass.mt_type, subclass.bl_label, "")
                enum_items.append(enum)
        return sorted(enum_items)

    invoked: BoolProperty(
        name="Invoked",
        default=False
    )

    executed: BoolProperty(
        name="Executed",
        default=False,
        description="Whether the tile generator has been executed"
    )

    base_updated: BoolProperty(
        name="Base Updated",
        default=True
    )

    refresh: BoolProperty(
        name="Refresh",
        default=False,
        description="Refresh")

    auto_refresh: BoolProperty(
        name="Auto",
        default=True,
        description="Automatic Refresh")

    reset_defaults: BoolProperty(
        name="Reset Defaults",
        default=False,
        description="Reset Defaults",
    )

    defaults_upated: BoolProperty(
        name="Defaults Updated",
        default=False
    )

    main_part_blueprint: EnumProperty(
        items=create_main_part_blueprint_enums,
        # update=update_part_defaults,
        name="Main")

    base_blueprint: EnumProperty(
        items=create_base_blueprint_enums,
        update=update_part_defaults,
        name="Base"
    )

    # Tile proportions
    x_proportionate_scale: BoolProperty(
        name="X",
        default=True
    )

    y_proportionate_scale: BoolProperty(
        name="Y",
        default=False
    )

    z_proportionate_scale: BoolProperty(
        name="Z",
        default=False
    )

    tile_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=2,
        update=tile_x_update,
        min=0
    )

    tile_y: FloatProperty(
        name="Y",
        default=0.3,
        step=50,
        precision=2,
        update=tile_y_update,
        min=0
    )

    tile_z: FloatProperty(
        name="Z",
        default=2.0,
        step=50,
        precision=2,
        update=tile_z_update,
        min=0
    )

    # Base size
    base_x: FloatProperty(
        name="X",
        default=2.0,
        step=50,
        precision=2,
        min=0
    )

    base_y: FloatProperty(
        name="Y",
        default=0.5,
        step=50,
        precision=2,
        min=0
    )

    base_z: FloatProperty(
        name="Z",
        default=0.3,
        step=50,
        precision=2,
        min=0
    )

    tile_size: FloatVectorProperty(
        name="Tile Size"
    )

    base_size: FloatVectorProperty(
        name="Base size"
    )

    collection_type: EnumProperty(
        items=collection_types,
        name="Collection Types",
        description="Easy way of distinguishing whether we are dealing with a tile, \
            an architectural element or a larger prefab such as a building or dungeon."
    )

    tile_name: StringProperty(
        name="Tile Name"
    )

    is_mt_collection: BoolProperty(
        default=True
    )

    converter_material: EnumProperty(
        items=create_material_enums,
        name="Material",
        description="Material to apply to converted object"
    )
    export_subdivs: IntProperty(
        name="Export Subdivisions",
        description="Subdivision levels of exported tile",
        default=3
    )
    # Native Subdivisions
    subdivision_density: EnumProperty(
        items=[
            ("HIGH", "High", "", 1),
            ("MEDIUM", "Medium", "", 2),
            ("LOW", "Low", "", 3)],
        default="MEDIUM",
        name="Subdivision Density")

    # UV smart projection correction
    UV_island_margin: FloatProperty(
        name="UV Margin",
        default=0.012,
        min=0,
        step=0.01,
        description="Tweak this if you have gaps at edges of tiles when you Make3D"
    )

    # stops texture projecting beyond bounds of vert group
    texture_margin: FloatProperty(
        name="Texture Margin",
        description="Margin around displacement texture. Used for correcting distortion",
        default=0.001,
        min=0.0001,
        soft_max=0.1,
        step=0.0001
    )

    tile_units: EnumProperty(
        name="Tile Units",
        items=units
    )

    base_socket_type: EnumProperty(
        items=[
            ("OPENLOCK", "OpenLOCK", ""),
            ("LASTLOCK", "LastLOCK", "")],
        default="OPENLOCK",
        name="Base socket type",
        description="What type of base socket to use."
    )
    
    generate_suppports: BoolProperty(
        default=True,
        name="Generate Supports",
        description="If checked, openlock connectors will have supports generated for them."
    )

    @classmethod
    def poll(cls, context):
        """Check in object mode."""
        if context.object is not None:
            return context.object.mode == 'OBJECT'
        else:
            return True

    def __init__(self):
        """Initialise."""
        self.cursor_orig_loc = (0, 0, 0)
        self.cursor_orig_rot = (0, 0, 0)

    def invoke(self, context, event):
        """Call when operator is invoked directly from the UI."""
        self.invoked = True
        self.reset_defaults = False

        scene_props = context.scene.mt_scene_props
        all_annotations = get_annotations(self.__class__)
        for key in scene_props.__annotations__.keys():
            for k in all_annotations.keys():
                try:
                    if k == key:
                        setattr(self, str(k), getattr(scene_props, str(k)))
                except TypeError:
                    pass
        self.refresh = True
        return self.execute(context)

    def execute(self, context):
        """Call when operator is executed."""
        self.init(context)

    def init(self, context):
        """Initialise operator properties."""
        deselect_all()
        self.executed = False
        scene = context.scene
        scene_props = scene.mt_scene_props
        tile_type = scene_props.tile_type

        # reset tile defaults
        if self.reset_defaults:
            tile_defaults = load_tile_defaults(context)
            for tile in tile_defaults:
                if tile['type'] == tile_type:
                    defaults = tile['defaults']
                    for key, value in defaults.items():
                        setattr(self, key, value)
                    break
            main_part_blueprint = self.main_part_blueprint
            base_blueprint = self.base_blueprint
            try:
                main_part_defaults = defaults['tile_defaults']
                for key, value in main_part_defaults.items():
                    if key == main_part_blueprint:
                        for k, v in value.items():
                            setattr(self, k, v)
                        break
            except KeyError:
                pass
            try:
                base_defaults = defaults['base_defaults']
                for key, value in base_defaults.items():
                    if key == base_blueprint:
                        for k, v in value.items():
                            setattr(self, k, v)
                        break
            except KeyError:
                pass
            self.reset_defaults = False

        # We create tile at origin and then move it back to original location.
        # This saves us having to update the scene when we reset origins etc.
        cursor = scene.cursor
        self.cursor_orig_loc = cursor.location.copy()
        self.cursor_orig_rot = cursor.rotation_euler.copy()
        cursor.location = (0, 0, 0)
        cursor.rotation_euler = (0, 0, 0)

        # create helper object for material mapping
        create_helper_object(context)

        # Each tile is a sub collection of a 'Tiles' collection
        collections = bpy.data.collections
        if 'Tiles' not in collections:
            create_collection('Tiles', scene.collection)
        tile_collection = collections.new(scene_props.tile_type.lower())
        collections['Tiles'].children.link(tile_collection)

        # set tile_name to collection name
        self.tile_name = tile_collection.name

        # properties are stored on the tile collection for
        # later access by the tile constructors
        tile_props = tile_collection.mt_tile_props

        self_annotations = get_annotations(self.__class__)
        try:
            copy_annotation_props(self, tile_props, self_annotations)
        except TypeError as err:
            self.report({'INFO'}, str(err))
            return False

        tile_props.tile_type = tile_type
        activate_collection(tile_collection.name)
        return True

    def get_base_socket_filename(self):
        """Return the filename where booleans are stored for the tile's base_socket_type.

        Returns:
            str: filename
        """
        sockets = [
            {'socket_type': 'OPENLOCK',
             'filename': "openlock.blend" if self.generate_suppports else "openlockNoSupport.blend"},
            {'socket_type': 'LASTLOCK',
             'filename': 'lastlock.blend'}]
        for socket in sockets:
            if socket['socket_type'] == self.base_socket_type:
                return socket['filename']
        return False

    def delete_tile_collection(self, col_name):
        """Delete the collection and any objects it contains.
        Use for cleaning up on error.

        Args:
            col_name (str): collection name
        """
        objects = bpy.data.objects
        collections = bpy.data.collections
        try:
            collection = collections[col_name]
            for obj in collections[col_name].objects:
                bpy.data.objects.remove(objects[obj.name], do_unlink=True)
            collections.remove(collections[collection.name], do_unlink=True)
            return True
        except KeyError as err:
            self.report({'INFO'}, str(err))
            return False

    def finalise_tile(self, context, base, *args):
        """Finalise the tile.

        Parents the objects passed in *args to the base, sets the base material,
        places the tile at the cursor location and resets the cursor.

        Args:
            context (bpy.context): Context
            base (bpy.types.Object): Base to parent objects to
            *args (list of bpy.types.Object)
        """
        # assign secondary material to base if it is a mesh
        prefs = get_prefs()
        if base.type == 'MESH' and prefs.secondary_material not in base.material_slots:
            base.data.materials.append(
                bpy.data.materials[prefs.secondary_material])

        # Reset location of base
        base.location = self.cursor_orig_loc
        cursor = context.scene.cursor
        cursor.location = self.cursor_orig_loc
        cursor.rotation_euler = self.cursor_orig_rot

        # Parent cores to base
        for arg in args:
            if arg is not None:
                arg.parent = base
                lock_all_transforms(arg)

        # deselect any currently selected objects
        for obj in context.selected_objects:
            obj.select_set(False)

        base.select_set(True)
        context.view_layer.objects.active = base

        if self.auto_refresh is False:
            self.refresh = False

        self.invoked = False
        self.executed = True

    def draw(self, context):
        """Draw the Redo panel."""
        layout = self.layout
        if self.auto_refresh is False:
            self.refresh = False
        elif self.auto_refresh is True:
            self.refresh = True

        # Refresh options
        row = layout.box().row()
        split = row.split()
        split.scale_y = 1.5
        split.prop(self, "auto_refresh", toggle=True,
                   icon_only=True, icon='AUTO')
        split.prop(self, "refresh", toggle=True,
                   icon_only=True, icon='FILE_REFRESH')
        layout.prop(self, 'reset_defaults', toggle=True, icon='LOOP_BACK')
        layout.prop(self, 'subdivision_density')


@multimethod(str, dict)
def get_subdivs(density, dims):
    """Get the number of times to subdivide each side when drawing.

    Args:
        density (ENUM in {'LOW', 'MEDIUM', 'HIGH'}): Density of subdivision
        dims (dict): Dimensions

    Returns:
        [list(int, int, int)]: subdivisions
    """
    subdivs = {}
    if density == 'LOW':
        multiplier = 4
    elif density == 'MEDIUM':
        multiplier = 8
    elif density == 'HIGH':
        multiplier = 16

    for k, v in dims.items():
        v = floor(v * multiplier)
        if v == 0:
            v = v + 1
        subdivs[k] = v
    return subdivs


@multimethod(str, list)
def get_subdivs(density, base_dims):
    """Get the number of times to subdivide each side when drawing.

    Args:
        density (ENUM in {'LOW', 'MEDIUM', 'HIGH'}): Density of subdivision
        base_dims (list(float, float, float)): Base dimensions

    Returns:
        [list(int)]: subdivisions
    """
    subdivs = []
    for x in base_dims:
        if density == 'LOW':
            multiplier = 4
        elif density == 'MEDIUM':
            multiplier = 8
        elif density == 'HIGH':
            multiplier = 16
    for x in base_dims:
        x = floor(x * multiplier)
        subdivs.append(x)
    subdivs = [x + 1 if x == 0 else x for x in subdivs]
    return subdivs


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
    copy_annotation_props(scene_props, tile_props)

    tile_props.tile_name = tile_collection.name
    tile_props.is_mt_collection = True
    tile_props.collection_type = "TILE"


def copy_annotation_props(source_props, target_props, source_annotations=None, target_annotations=None):
    """Set target_props to the value of source_props.

    Props must have same names and be of same type. If you want to include annotations of parent
    class(es) set them seperately.

    Args:
        source_prop_group (class): Source class
        target_prop_group (class): Target class
        source_annotations (.__annotations__), optional: annotations to copy. Defaults to None.
        target_annotations (.__annotations__), optional: annotations to set. Defaults to None.
    """
    if not source_annotations:
        source_annotations = source_props.__annotations__
    if not target_annotations:
        target_annotations = target_props.__annotations__

    for key in source_annotations.keys():
        for k in target_annotations.keys():
            if k == key:
                try:
                    setattr(target_props, str(k),
                            getattr(source_props, str(k)))
                except TypeError:
                    pass


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


def add_subsurf_modifier(obj):
    """Add a subsurf modifier for material system and store its name in object props.

    Args:
        obj (bpy.types.object): object

    Returns:
        str: subsurf name
    """
    subsurf = obj.modifiers.new('MT Subsurf', 'SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    obj.mt_object_props.subsurf_mod_name = subsurf.name
    obj.cycles.use_adaptive_subdivision = True

    return subsurf.name


def convert_to_displacement_core(core, textured_vertex_groups, material, subsurf):
    """Convert the core part of an object so it can be used by the MakeTile dispacement system.

    If possible pass in an already created subsurf modifier.

    Args:
        core (bpy.types.Object): object to convert
        textured_vertex_groups (list[str]): list of vertex group names that should have a texture applied
        material (str): Name of material to use
        subsurf (str): Name of subsurf modifier
    """
    context = bpy.context
    scene = context.scene
    prefs = get_prefs()
    props = core.mt_object_props
    scene_props = scene.mt_scene_props
    prim_mat = bpy.data.materials[material]
    sec_mat = bpy.data.materials[prefs.secondary_material]

    # check if we need to append primary material
    if prefs.default_mat_behaviour == 'APPEND' and prim_mat.library:
        new_mat = prim_mat.copy()
        bpy.data.materials.remove(prim_mat)
        prim_mat = new_mat

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
    vert_group = construct_displacement_mod_vert_group(
        core, textured_vertex_groups)
    disp_mod.vertex_group = vert_group

    # create texture for displacement modifier
    props.disp_texture = bpy.data.textures.new(core.name + '.texture', 'IMAGE')

    subsurf = core.modifiers[subsurf]
    # switch off subsurf modifier if we are not in cycles mode
    if bpy.context.scene.render.engine != 'CYCLES':
        subsurf.show_viewport = False

    subsurf.levels = 3

    # assign materials
    if sec_mat.name not in core.data.materials:
        core.data.materials.append(sec_mat)

    if prim_mat.name not in core.data.materials:
        core.data.materials.append(prim_mat)

    for group in textured_vertex_groups:
        assign_mat_to_vert_group(group, core, prim_mat)

    # flag core as a displacement object
    core.mt_object_props.is_displacement = True
    core.mt_object_props.geometry_type = 'CORE'


def spawn_empty_base(tile_props):
    """Spawn an empty base into the scene.

    Args:
        tile_props (MakeTile.properties.MT_Tile_Properties): tile properties

    Returns:
        bpy.types.Object: Empty
    """
    tile_name = tile_props.tile_name
    base = bpy.data.objects.new(tile_name + '.base', None)
    base.name = tile_name + '.base'
    add_object_to_collection(base, tile_name)
    obj_props = base.mt_object_props
    obj_props.is_mt_object = True
    obj_props.geometry_type = 'BASE'
    obj_props.tile_name = tile_name
    base.show_in_front = True

    bpy.context.view_layer.objects.active = base
    return base


def spawn_prefab(context, subclasses, blueprint, mt_type, **kwargs):
    """Spawn a maketile prefab such as a base or tile core(s).

    Args:
        context (bpy.context): Blender context
        subclasses (list): list of all subclasses of MT_Tile_Generator
        blueprint (str): mt_blueprint enum item
        type (str): mt_type enum item
        **kwargs (dict): Arguments to pass to operator

    Returns:
        bpy.types.Object: Prefab
    """
    args = []
    for key, value in kwargs.items():
        if isinstance(value, str):
            value = "\"" + value + "\""
        args.append(key + '=' + str(value))
    arg_str = ', '.join(args)

    # ensure we can only run bpy.ops in our eval statements
    allowed_names = {k: v for k, v in bpy.__dict__.items() if k == 'ops'}
    for subclass in subclasses:
        if hasattr(subclass, 'mt_type') and hasattr(subclass, 'mt_blueprint'):
            if subclass.mt_type == mt_type and subclass.mt_blueprint == blueprint:
                eval_str = 'ops.' + subclass.bl_idname + '(' + arg_str + ')'
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
        "openlock.blend" if tile_props.generate_suppports else "openlockNoSupport.blend")

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
    if bool_obj.parent:
        matrix_copy = bool_obj.matrix_world.copy()
        bool_obj.parent = None
        bool_obj.matrix_world = matrix_copy

    bool_obj.parent = parent_obj
    bool_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

    bool_obj.display_type = 'BOUNDS'
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
    # bpy.context.view_layer.update()
    cutter_coll_item.parent = target_obj.name
