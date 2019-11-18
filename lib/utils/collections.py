import bpy


def create_collection(collection_name, collection_parent):
    """Checks to see if a collection exists and if not creates it"""
    if collection_name not in bpy.data.collections:
        new_collection = bpy.data.collections.new(collection_name)
        # links collection to parent collection
        collection_parent.children.link(new_collection)
        return new_collection
    return bpy.data.collections[collection_name]


def add_object_to_collection(obj, collection_name):
    """Adds an object to a collection, checking to see if
    obj is already in collection
    """
    if not (obj.name, obj) in bpy.data.collections[collection_name].objects.items():
        bpy.data.collections[collection_name].objects.link(obj)
    return {'FINISHED'}


def get_collection(layer_collection, collection_name):
    """Recursively searches for a layer collection and returns it.
    God knows why this isn't part of the API!
    """
    found = None
    if (layer_collection.name == collection_name):
        return layer_collection
    for layer in layer_collection.children:
        found = get_collection(layer_collection, collection_name)
        if found:
            return found
