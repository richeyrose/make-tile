import bpy
from ..lib.utils.collections import add_object_to_collection, create_collection


class MT_OT_Assign_Reference_Object(bpy.types.Operator):
    bl_idname = "material.assign_reference_object"
    bl_label = "assign_reference_object"

    def execute(self, context):
        # Helper object collection
        helper_collection = create_collection('MT Helpers', context.scene.collection)

        # Add an empty used as a reference object for material projection
        if 'Material Helper Empty' not in bpy.data.objects:
            material_helper = bpy.data.objects.new('Material Helper Empty', None)
            material_helper.hide_viewport = True
            add_object_to_collection(material_helper, helper_collection.name)
            assign_obj_to_obj_texture_coords(material_helper)

        return {'FINISHED'}


def assign_obj_to_obj_texture_coords(obj):
    """Use to fix error in wrap around material projection when objects are rotated.

    Args:
        obj (bpy.types.object): reference object to use for material object texture coordinates
    """
    for mat in bpy.data.materials:
        if hasattr(mat.node_tree, 'nodes'):
            nodes = mat.node_tree.nodes
            text_coord_nodes = [node for node in nodes if node.type == 'TEX_COORD']
            for node in text_coord_nodes:
                if hasattr(node.parent, 'name'):
                    if node.parent.name == 'Root Nodes':
                        node.object = obj
