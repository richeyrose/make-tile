import bpy
from bpy.props import BoolProperty, EnumProperty
from .. lib.utils.collections import get_objects_owning_collections
from ..tile_creation.create_tile import (
    set_bool_props)


class MT_OT_Add_Collection_To_Tile(bpy.types.Operator):
    """
    Add objects contained in a collection to a tile so they are exported with the tile.

    Adds objects from all collections the second to last selected object belongs to, to the active_object's
    tile collection. Objects with boolean_type 'DIFFERENCE' are added as booleans to all objects in the
    tile collection with the geometry_type 'CORE'. The operands are also parented to the tile collection base.
    """

    bl_idname = "collection.add_collection_to_tile"
    bl_label = "Add collection To Tile"
    bl_description = "Adds objects from all collections the second to last selected object belongs to, to the active_object's tile collection."
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
        filtered_obs = [obj for obj in selected_objects if obj is not active_object]
        operands = set()
        for obj in filtered_obs:
            operand_collections = get_objects_owning_collections(obj.name)
            for coll in operand_collections:
                if coll is not tile_collection:
                    operands.update(coll.objects.values())

        mesh_operands = sorted([obj for obj in operands if obj.type == 'MESH'], key=lambda obj: obj.mt_object_props.boolean_order)

        for obj in mesh_operands:
            if obj.name not in tile_collection.objects:
                # add booleans for all operand objects of 'DIFFERENCE' boolean type.
                if obj.mt_object_props.boolean_type == 'DIFFERENCE':
                    for core in cores:
                        set_bool_props(obj, core, obj.mt_object_props.boolean_type, solver='FAST')
                    if base.type == 'MESH' and obj.mt_object_props.affects_base is True:
                        set_bool_props(obj, base, obj.mt_object_props.boolean_type, solver='FAST')
                    obj.hide_render = True
                    obj.display_type = 'BOUNDS'

        # other operands we just add to tile collection because boolean system is
        # unreliable and/or slow currently. Instead we deal with boolean unions by voxelisation on export
        for obj in operands:
            if obj.name not in tile_collection.objects:
                tile_collection.objects.link(obj)
                # we now parent any 'BASE' operands to tile collection 'BASE' so our architectural
                # element will move with the tile
                if obj.mt_object_props.geometry_type == 'BASE':
                    obj.parent = base
                    obj.matrix_parent_inverse = base.matrix_world.inverted()

        return {'FINISHED'}


class MT_OT_Add_Object_To_Tile(bpy.types.Operator):
    """Adds the selected object to the active object's tile collection.

    changes the selected object's type to ADDITIONAL and optionally parents selected
    to active and applies all modifiers
    """

    bl_idname = "object.add_to_tile"
    bl_label = "Add object to Tile"
    bl_options = {'REGISTER', 'UNDO'}

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers to object before adding it to tile?",
        default=True
    )

    boolean_type: EnumProperty(
        name="Boolean Type",
        items=[
            ("UNION", "Union", ""),
            ("DIFFERENCE", "Difference", "")
        ],
        default="UNION",
        description="Whether to add (Union) or subtract (Difference) object from tile."
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.mode == 'OBJECT' and obj.type == 'MESH'

    def execute(self, context):
        """Add the selected object(s) to the active object's tile collection."""

        objects_to_add = []

        active_object = context.active_object
        tile_collections = get_objects_owning_collections(active_object.name)

        for collection in tile_collections:
            if collection.mt_tile_props.collection_type == 'TILE':
                tile_collection = collection
                break

        base = None

        for obj in tile_collection.objects:
            if obj.mt_object_props.geometry_type == 'BASE':
                base = obj
                break

        cores = set([obj for obj in tile_collection.objects if obj.mt_object_props.geometry_type == 'CORE'])

        for obj in context.selected_objects:
            if obj != context.active_object:
                objects_to_add.append(obj)

                # change geometry type and tile name props
                obj.mt_object_props.geometry_type = 'ADDITIONAL'
                obj.mt_object_props.tile_name = tile_collection.name
                obj.mt_object_props.boolean_type = self.boolean_type

                # unlink from current collections
                current_collections = get_objects_owning_collections(obj.name)
                for coll in current_collections:
                    coll.objects.unlink(obj)

                # add to new tile collection
                tile_collection.objects.link(obj)

        # apply modifiers if necessary
        if self.apply_modifiers is True:
            depsgraph = context.evaluated_depsgraph_get()
            for obj in objects_to_add:
                if len(obj.modifiers) > 0:
                    object_eval = obj.evaluated_get(depsgraph)
                    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
                    obj.modifiers.clear()
                    obj.data = mesh_from_eval

        # parent objects to base
        for obj in objects_to_add:
            if obj.parent:
                matrix_copy = obj.matrix_world.copy()
                obj.parent = None
                obj.matrix_world = matrix_copy
            if base:
                obj.parent = base
                obj.matrix_parent_inverse = base.matrix_world.inverted()
            # add as difference boolean if boolean_type is DIFFERENCE
            if obj.mt_object_props.boolean_type == 'DIFFERENCE':
                for core in cores:
                    set_bool_props(obj, core, obj.mt_object_props.boolean_type, solver='FAST')
                if base and base.type == 'MESH' and obj.mt_object_props.affects_base is True:
                    set_bool_props(obj, base, obj.mt_object_props.boolean_type, solver='FAST')

                obj.hide_render = True
                obj.display_type = 'BOUNDS'

        return {'FINISHED'}

    def invoke(self, context, event):
        """Call when operator invoked from UI."""
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context)        :
        """Draw popup property menu."""
        layout = self.layout
        layout.prop(self, 'apply_modifiers')
        layout.prop(self, 'boolean_type')


def add_to_tile_object_context_menu_items(self, context):
    """Add options to object context (right click) menu."""
    layout = self.layout
    try:
        if context.active_object.type in ['MESH']:
            layout.separator()
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("object.add_to_tile", text="Add / Subtract object from Tile")
            layout.operator("collection.add_collection_to_tile")
    except AttributeError:
        pass


def register():
    """Register aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.append(add_to_tile_object_context_menu_items)


def unregister():
    """Unregister aditional options in object context (right click) menu."""
    bpy.types.VIEW3D_MT_object_context_menu.remove(add_to_tile_object_context_menu_items)
