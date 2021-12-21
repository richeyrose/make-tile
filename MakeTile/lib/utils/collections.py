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


def get_collection(gp_collection, collection_name):
    """Recursively searches for a layer collection and returns it.
    God knows why this isn't part of the API!
    Keywords -- gp_collection -- Grandparent collection
    """
    found = None
    if (gp_collection.name == collection_name):
        return gp_collection
    for layer in gp_collection.children:
        found = get_collection(layer, collection_name)
        if found:
            return found


def activate_collection(collection_name):
    """Activates the passed in collection."""
    collection = get_collection(bpy.context.view_layer.layer_collection, collection_name)
    bpy.context.view_layer.active_layer_collection = collection
    return collection


def get_objects_owning_collections(object_name):
    """Return a list of collections the object is a member of.

    Args:
        object_name (str): object_name

    Returns:
        list(bpy.types.Collection): list of collections
    """
    collections = []

    for coll in bpy.data.collections:
        if object_name in coll.objects:
            collections.append(coll)

    return collections
