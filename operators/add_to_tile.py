import bpy
import addon_utils
from .. lib.utils.collections import get_objects_owning_collections
from ..tile_creation.create_tile import (
    set_bool_props,
    set_bool_obj_props)
from .flatten_tile import flatten_tile
from .voxeliser import voxelise, make_manifold
from .decimator import decimate
from ..lib.utils.selection import deselect_all, select, activate


class MT_OT_Add_Architectural_Element_To_Tile(bpy.types.Operator):
    """
    Add architectural elements contained in a collection to a tile so they are exported with the tile.

    Adds objects from all collections the second to last selected object belongs to, to the active_object's
    tile collection. Objects with boolean_type 'DIFFERENCE' are added as booleans to all objects in the
    tile collection with the geometry_type 'CORE'. The operands are also parented to the tile collection base.
    """

    bl_idname = "collection.add_arch_elem_to_tile"
    bl_label = "Add Architectural Element To Tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        selected_objects = context.selected_objects

        # first check if there is more than one object selected
        if len(selected_objects) > 1:
            active_object = context.active_object

            # check that the active object belongs to a tile collection
            tile_collections = get_objects_owning_collections(active_object.name)

            for collection in tile_collections:
                if collection.mt_tile_props.collection_type == 'TILE':
                    return True

        return False


    def execute(self, context):
        """Execute the operator.

        Adds objects from all collections the second to last selected object belongs to, to the active_object's
        tile collection. Objects with boolean_type 'DIFFERENCE' are added as booleans to all objects in the
        tile collection with the geometry_type 'CORE'. The operands are also parented to the tile collection base.
        """
        selected_objects = context.selected_objects
        active_object = context.active_object

        tile_collections = get_objects_owning_collections(active_object.name)

        for collection in tile_collections:
            if collection.mt_tile_props.collection_type == 'TILE':
                tile_collection = collection
                break

        base = None
        cores = set([obj for obj in tile_collection.objects if obj.mt_object_props.geometry_type == 'CORE'])

        for obj in tile_collection.objects:
            if obj.mt_object_props.geometry_type == 'BASE':
                base = obj
                break

        # get all mesh objects to be added to tile collection
        operand_collections = get_objects_owning_collections(selected_objects[-2].name)
        operands = set()
        for coll in operand_collections:
            operands.update(coll.objects.values())

        mesh_operands = sorted([obj for obj in operands if obj.type == 'MESH'], key=lambda obj: obj.mt_object_props.boolean_order)

        for obj in mesh_operands:
            # add booleans for all operand objects of 'DIFFERENCE' boolean type.
            if obj.mt_object_props.boolean_type == 'DIFFERENCE':
                for core in cores:
                    set_bool_props(obj, core, obj.mt_object_props.boolean_type, solver='FAST')
                if base.type == 'MESH' and obj.mt_object_props.affects_base is True:
                    set_bool_props(obj, base, obj.mt_object_props.boolean_type, solver='FAST')

                obj.hide_render = True
                obj.hide_viewport = True

        # other operands we just add to tile collection because boolean system is
        # unreliable and/or slow currently. Instead we deal with boolean unions by voxelisation on export
        for obj in operands:
            tile_collection.objects.link(obj)
            # we now parent any 'BASE' operands to tile collection 'BASE' so our architectural
            # element will move with the tile
            if obj.mt_object_props.geometry_type == 'BASE':
                obj.parent = base
                obj.matrix_parent_inverse = base.matrix_world.inverted()

        return {'FINISHED'}


class MT_OT_Add_Object_To_Tile(bpy.types.Operator):
    """Adds the selected object to the active object's tile collection,
    changes the selected object's type to ADDITIONAL and optionally parents selected
    to active and applies all modifiers"""

    bl_idname = "object.add_to_tile"
    bl_label = "Add to Tile"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.mt_object_props.is_mt_object is True

    def execute(self, context):
        objects_to_add = []
        collection = bpy.data.collections[context.active_object.mt_object_props.tile_name]

        for obj in context.selected_objects:
            if obj != context.active_object:
                objects_to_add.append(obj)
                # change geometry type and tile name props
                obj.mt_object_props.geometry_type = 'ADDITIONAL'
                obj.mt_object_props.tile_name = collection.name

                # unlink from current collections
                current_collections = get_objects_owning_collections(obj.name)
                for coll in current_collections:
                    coll.objects.unlink(obj)

                # add to new tile collection
                collection.objects.link(obj)

        # apply modifiers if necessary
        if context.scene.mt_apply_modifiers is True:
            depsgraph = context.evaluated_depsgraph_get()
            for obj in objects_to_add:
                object_eval = obj.evaluated_get(depsgraph)
                mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                obj.modifiers.clear()
                obj.data = mesh_from_eval

        # parent object to tile's base object
        parent = None
        for obj in collection.all_objects:
            if obj.mt_object_props.geometry_type == 'BASE':
                parent = obj

        ctx = {
            'selected_objects': objects_to_add,
            'selectable_objects': objects_to_add,
            'selected_editable_objects': objects_to_add,
            'active_object': parent,
            'object': parent
        }

        for obj in objects_to_add:
            bpy.ops.object.parent_set(ctx, type='OBJECT', keep_transform=True)


        return {'FINISHED'}

    @classmethod
    def register(cls):
        bpy.types.Scene.mt_apply_modifiers = bpy.props.BoolProperty(
            name="Apply Modifiers",
            description="This will apply all modifiers to the object before \
                adding it to the selected tile",
            default=True)

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.mt_apply_modifiers
