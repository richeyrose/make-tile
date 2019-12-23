"""Contains operator class to make tiles"""
import os
import bpy
import bpy.utils.previews
from mathutils import Vector
from .. lib.utils.selection import deselect_all
from .. utils.registration import get_path, get_prefs
from .. lib.utils.collections import (
    create_collection,
    activate_collection)

from .. enums.enums import (
    tile_main_systems,
    tile_types,
    units,
    base_systems,
    tile_blueprints,
    base_socket_side)

from .. materials.materials import (
    load_materials,
    get_blend_filenames,
    update_displacement_material_2,
    update_preview_material_2)

from .. tile_creation.create_straight_wall_tile import create_straight_wall
from .. tile_creation.create_floor_tile import create_rectangular_floor
from .. tile_creation.create_curved_wall_tile import create_curved_wall
from .. tile_creation.create_corner_wall import create_corner_wall
from .. tile_creation.create_triangular_floor import create_triangular_floor


class MT_OT_Make_Tile(bpy.types.Operator):
    """Operator class used to create tiles"""
    bl_idname = "scene.make_tile"
    bl_label = "Create a tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if bpy.context.object is not None:
            return bpy.context.object.mode == 'OBJECT'
        else:
            return True

    def execute(self, context):

        ############################################
        # Set defaults for different tile systems #
        ############################################

        tile_blueprint = context.scene.mt_tile_blueprint
        tile_type = context.scene.mt_tile_type

        if tile_blueprint == 'OPENLOCK':
            context.scene.mt_main_part_blueprint = 'OPENLOCK'
            context.scene.mt_base_blueprint = 'OPENLOCK'

        if tile_blueprint == 'PLAIN':
            context.scene.mt_main_part_blueprint = 'PLAIN'
            context.scene.mt_base_blueprint = 'PLAIN'

        #######################################
        # Create our collection and tile name #
        # 'Tiles' are collections of meshes   #
        # parented to an empty                #
        #######################################

        scene_collection = bpy.context.scene.collection

        # Check to see if tile collection exist and create if not
        tiles_collection = create_collection('Tiles', scene_collection)

        # construct first part of tile name based on system and type
        tile_name = tile_blueprint.lower() + "." + tile_type.lower()
        deselect_all()

        if tile_type == 'STRAIGHT_WALL' or 'CURVED_WALL' or 'CORNER_WALL':
            # create walls collection if it doesn't already exist
            walls_collection = create_collection('Walls', tiles_collection)

            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Walls'].children.link(tile_collection)

        if tile_type == 'RECTANGULAR_FLOOR' or 'TRIANGULAR_FLOOR':
            # create floor collection if one doesn't already exist
            floors_collection = create_collection('Floors', tiles_collection)
            # create new collection that operates as our "tile" and activate it
            tile_collection = bpy.data.collections.new(tile_name)
            bpy.data.collections['Floors'].children.link(tile_collection)

        # make final tile name
        activate_collection(tile_collection.name)

        tile_name = tile_collection.name

        #####################
        # Create Tile Empty #
        #####################

        tile_empty = bpy.data.objects.new(tile_name + ".empty", None)
        bpy.context.layer_collection.collection.objects.link(tile_empty)

        ###################################
        #  Package up our tile properties #
        # and store them on our empty     #
        ###################################

        tile_size = Vector((
            context.scene.mt_tile_x,
            context.scene.mt_tile_y,
            context.scene.mt_tile_z))

        base_size = Vector((
            context.scene.mt_base_x,
            context.scene.mt_base_y,
            context.scene.mt_base_z))

        tile_materials = {
            'tile_material_1': context.scene.mt_tile_material_1,
            'tile_material_2': context.scene.mt_tile_material_2
        }

        textured_faces = {
            "x_neg": context.scene.mt_x_neg_textured,
            "x_pos": context.scene.mt_x_pos_textured,
            "y_pos": context.scene.mt_y_pos_textured,
            "y_neg": context.scene.mt_y_neg_textured,
            "z_pos": context.scene.mt_z_pos_textured,
            "z_neg": context.scene.mt_z_neg_textured,
        }

        tile_empty['tile_properties'] = {
            'tile_name': tile_name,
            'empty_name': tile_empty.name,
            'tile_blueprint': context.scene.mt_tile_blueprint,
            'base_blueprint': context.scene.mt_base_blueprint,
            'main_part_blueprint': context.scene.mt_main_part_blueprint,
            'tile_type': context.scene.mt_tile_type,
            'tile_size': tile_size,
            'base_size': base_size,
            'tile_materials': tile_materials,
            'textured_faces': textured_faces,
            'base_inner_radius': context.scene.mt_base_inner_radius,  # used for curved tiles only
            'wall_inner_radius': context.scene.mt_wall_inner_radius,  # used for curved walls only
            'degrees_of_arc': context.scene.mt_degrees_of_arc,  # used for curved tiles only
            'segments': context.scene.mt_segments,  # used for curved tiles only
            'base_socket_sides': context.scene.mt_base_socket_side,  # used for bases that can or should have sockets only on certain sides
            'trimmers': {},  # used to trim sides of tile on voxelisation and export
            'angle_1': context.scene.mt_angle_1,  # used for corner walls & triangular floors
            'x_leg': context.scene.mt_x_leg_len,  # used for corner walls & triangular floors
            'y_leg': context.scene.mt_y_leg_len,  # used for corner walls & triangular floors
        }

        ###############
        # Create Tile #
        ###############

        if tile_type == 'STRAIGHT_WALL':
            create_straight_wall(tile_empty)

        if tile_type == 'CURVED_WALL':
            create_curved_wall(tile_empty)

        if tile_type == 'CORNER_WALL':
            create_corner_wall(tile_empty)

        if tile_type == 'RECTANGULAR_FLOOR':
            create_rectangular_floor(tile_empty)

        if tile_type == 'TRIANGULAR_FLOOR':
            create_triangular_floor(tile_empty)

        return {'FINISHED'}

    @classmethod
    def register(cls):
        print("Registered class: %s " % cls.bl_label)

        preferences = get_prefs()
        material_enum_collection = bpy.utils.previews.new()
        material_enum_collection.directory = ''
        material_enum_collection.enums = ()
        enum_collections["materials"] = material_enum_collection

        bpy.types.Scene.mt_tile_name = bpy.props.StringProperty(
            name="Tile Name",
            default="Tile"
        )

        bpy.types.Scene.mt_tile_units = bpy.props.EnumProperty(
            items=units,
            name="Units",
            default=preferences.default_units,
        )

        bpy.types.Scene.mt_tile_blueprint = bpy.props.EnumProperty(
            items=tile_blueprints,
            name="Blueprint",
            default=preferences.default_tile_blueprint,
        )

        bpy.types.Scene.mt_main_part_blueprint = bpy.props.EnumProperty(
            items=tile_main_systems,
            name="Main System",
            default=preferences.default_tile_main_system,
        )
        bpy.types.Scene.mt_tile_type = bpy.props.EnumProperty(
            items=tile_types,
            name="Type",
            default="STRAIGHT_WALL",
        )

        bpy.types.Scene.mt_base_blueprint = bpy.props.EnumProperty(
            items=base_systems,
            name="Base Type",
            default=preferences.default_base_system,
        )

        bpy.types.Scene.mt_tile_material_1 = bpy.props.EnumProperty(
            items=load_material_enums,
            name="Material 1",
            update=update_material_1,
        )

        bpy.types.Scene.mt_tile_material_2 = bpy.props.EnumProperty(
            items=load_material_enums,
            name="Material 2",
            update=update_material_2,
        )

        bpy.types.Scene.mt_tile_resolution = bpy.props.IntProperty(
            name="Resolution",
            description="Bake resolution of displacement maps. Higher = better quality but slower",
            default=1024,
            min=1024,
            max=8192,
            step=1024,
        )

        bpy.types.Scene.mt_subdivisions = bpy.props.IntProperty(
            name="Subdivisions",
            description="How many times to subdivide the displacement mesh. Higher = better but slower. \
            Going above 8 is really not recommended and may cause Blender to freeze up for a loooooong time!",
            default=6,
            soft_max=8,
        )

        # Which sides of walls to texture
        bpy.types.Scene.mt_y_neg_textured = bpy.props.BoolProperty(
            name="Inner",
            default=True
        )

        bpy.types.Scene.mt_y_pos_textured = bpy.props.BoolProperty(
            name="Outer",
            default=True
        )

        bpy.types.Scene.mt_z_pos_textured = bpy.props.BoolProperty(
            name="Top",
            default=True
        )

        bpy.types.Scene.mt_z_neg_textured = bpy.props.BoolProperty(
            name="Bottom",
            default=False
        )

        bpy.types.Scene.mt_x_neg_textured = bpy.props.BoolProperty(
            name="Left",
            default=False
        )

        bpy.types.Scene.mt_x_pos_textured = bpy.props.BoolProperty(
            name="Right",
            default=False
        )

        # Tile and base size. We use seperate floats so that we can only show
        # customisable ones where appropriate. These are wrapped up
        # in a vector and passed on as tile_size and base_size

        # Tile size
        bpy.types.Scene.mt_tile_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_y = bpy.props.FloatProperty(
            name="Y",
            default=2,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_tile_z = bpy.props.FloatProperty(
            name="Z",
            default=2.0,
            step=0.1,
            precision=3,
            min=0
        )

        # Base size
        bpy.types.Scene.mt_base_x = bpy.props.FloatProperty(
            name="X",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_base_y = bpy.props.FloatProperty(
            name="Y",
            default=0.5,
            step=0.5,
            precision=3,
            min=0
        )

        bpy.types.Scene.mt_base_z = bpy.props.FloatProperty(
            name="Z",
            default=0.3,
            step=0.1,
            precision=3,
            min=0
        )

        # Corner walll and triangular base specific
        bpy.types.Scene.mt_angle_1 = bpy.props.FloatProperty(
            name="Base Angle",
            default=90,
            step=5,
            precision=1
        )

        bpy.types.Scene.mt_x_leg_len = bpy.props.FloatProperty(
            name="Leg 1 Length",
            description="Length of leg",
            default=2,
            step=0.5,
            precision=2
        )

        bpy.types.Scene.mt_y_leg_len = bpy.props.FloatProperty(
            name="Leg 2 Length",
            description="Length of leg",
            default=2,
            step=0.5,
            precision=2
        )

        # Openlock curved wall specific
        bpy.types.Scene.mt_base_socket_side = bpy.props.EnumProperty(
            items=base_socket_side,
            name="Socket Side",
            default="INNER",
        )

        # Used for curved wall tiles
        bpy.types.Scene.mt_base_inner_radius = bpy.props.FloatProperty(
            name="Base inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0,
        )

        bpy.types.Scene.mt_wall_inner_radius = bpy.props.FloatProperty(
            name="Wall inner radius",
            default=2.0,
            step=0.5,
            precision=3,
            min=0
        )

        # TODO: Fix hack to make 360 curved wall work. Ideally this should merge everything
        bpy.types.Scene.mt_degrees_of_arc = bpy.props.FloatProperty(
            name="Degrees of arc",
            default=90,
            step=45,
            precision=1,
            max=359.999,
            min=-359.999
        )

        bpy.types.Scene.mt_segments = bpy.props.IntProperty(
            name="Number of segments",
            default=8,
        )

    @classmethod
    def unregister(cls):
        print("Unregistered class: %s" % cls.bl_label)
        del bpy.types.Scene.mt_y_neg_textured
        del bpy.types.Scene.mt_y_pos_textured
        del bpy.types.Scene.mt_z_pos_textured
        del bpy.types.Scene.mt_z_neg_textured
        del bpy.types.Scene.mt_x_neg_textured
        del bpy.types.Scene.mt_x_pos_textured
        del bpy.types.Scene.mt_tile_name
        del bpy.types.Scene.mt_segments
        del bpy.types.Scene.mt_base_inner_radius
        del bpy.types.Scene.mt_wall_inner_radius
        del bpy.types.Scene.mt_degrees_of_arc
        del bpy.types.Scene.mt_base_socket_side
        del bpy.types.Scene.mt_base_x
        del bpy.types.Scene.mt_base_y
        del bpy.types.Scene.mt_base_z
        del bpy.types.Scene.mt_tile_x
        del bpy.types.Scene.mt_tile_y
        del bpy.types.Scene.mt_tile_z
        del bpy.types.Scene.mt_base_blueprint
        del bpy.types.Scene.mt_tile_resolution
        del bpy.types.Scene.mt_tile_material_1
        del bpy.types.Scene.mt_tile_material_2
        del bpy.types.Scene.mt_tile_type
        del bpy.types.Scene.mt_tile_blueprint
        del bpy.types.Scene.mt_main_part_blueprint
        del bpy.types.Scene.mt_tile_units

        for pcoll in enum_collections.values():
            bpy.utils.previews.remove(pcoll)
        enum_collections.clear()


def load_material_enums(self, context):
    enum_items = []
    preferences = get_prefs()
    if context is None:
        return enum_items

    materials_path = os.path.join(preferences.assets_path, "materials")
    blend_filenames = get_blend_filenames(materials_path)
    enum_collection = enum_collections['materials']
    if materials_path == enum_collection.directory:
        return enum_collection.enums

    load_materials(materials_path, blend_filenames)
    materials = bpy.data.materials
    for material in materials:
        # prevent make-tile adding the default material to the list
        if material.name != 'Material':
            enum = (material.name, material.name, "")
            enum_items.append(enum)

    enum_collection.enums = enum_items
    enum_collection.directory = materials_path
    return enum_collection.enums


# TODO: Rewrite for two materials
def update_material_1(self, context):
    preview_obj = bpy.context.object

    if 'geometry_type' in preview_obj:
        if preview_obj['geometry_type'] == 'PREVIEW':
            disp_obj = preview_obj['linked_obj']

            update_displacement_material_2(disp_obj, bpy.context.scene.mt_tile_material_1)
            update_preview_material_2(preview_obj, bpy.context.scene.mt_tile_material_1)


def update_material_2(self, context):
    preview_obj = bpy.context.object

    if 'geometry_type' in preview_obj:
        if preview_obj['geometry_type'] == 'PREVIEW':
            disp_obj = preview_obj['linked_obj']

            update_displacement_material_2(disp_obj, bpy.context.scene.mt_tile_material_1)
            update_preview_material_2(preview_obj, bpy.context.scene.mt_tile_material_1)


enum_collections = {}
