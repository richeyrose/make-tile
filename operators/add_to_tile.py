import bpy
from .. lib.utils.collections import get_objects_owning_collections
from ..tile_creation.create_tile import (
    set_bool_props,
    set_bool_obj_props)


class MT_OT_Add_Architectural_Element_To_Tile(bpy.types.Operator):
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
            tile_collection = None

            for collection in tile_collections:
                if collection.mt_tile_props.collection_type == 'TILE':
                    tile_collection = collection
                    break

            # check that the last but one selected object belongs to a collection of type "ARCH_ELEM"
            operand = selected_objects[-2]
            operand_collections = get_objects_owning_collections(operand.name)
            operand_collection = None

            for coll in operand_collections:
                if coll.mt_tile_props.collection_type == 'ARCH_ELEMENT':
                    operand_collection = coll
                    break

            if tile_collection and operand_collection:
                return True

        return False

    def execute(self, context):
        selected_objects = context.selected_objects
        active_object = context.active_object

        # check that the active object belongs to a tile collection
        tile_collections = get_objects_owning_collections(active_object.name)
        tile_collection = None

        for collection in tile_collections:
            if collection.mt_tile_props.collection_type == 'TILE':
                tile_collection = collection
                break

        tile_props = tile_collection.mt_tile_props

        # check that the last but one selected object belongs to a collection of type "ARCH_ELEM"
        operand = selected_objects[-2]
        operand_collections = get_objects_owning_collections(operand.name)
        operand_collection = None

        for coll in operand_collections:
            if coll.mt_tile_props.collection_type == 'ARCH_ELEMENT':
                operand_collection = coll
                break

        # get root object for parenting operands to
        root = None
        for obj in tile_collection.objects:
            if obj.mt_object_props.geometry_type == 'BASE':
                root = obj
                break

        # get tile core which is what we'll boolean
        core = None
        for obj in tile_collection.objects:
            if obj.mt_object_props.geometry_type in ['CORE']:
                core = obj
                break

        # boolean objects from operand collection with tile core
        intersect_objects = [obj for obj in operand_collection.objects if obj.mt_object_props.geometry_type == 'INTERSECT']
        union_objects = [obj for obj in operand_collection.objects if obj.mt_object_props.geometry_type == 'UNION']
        diff_objects = [obj for obj in operand_collection.objects if obj.mt_object_props.geometry_type == 'DIFFERENCE']

        for obj in intersect_objects:
            set_bool_obj_props(obj, root, tile_props, 'INTERSECT')
            set_bool_props(obj, core, 'INTERSECT')

        for obj in diff_objects:
            set_bool_obj_props(obj, root, tile_props, 'DIFFERENCE')
            set_bool_props(obj, core, 'DIFFERENCE')

        for obj in union_objects:
            set_bool_obj_props(obj, root, tile_props, 'UNION')
            set_bool_props(obj, core, 'UNION')

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
