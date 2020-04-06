import os
import bpy
from bpy.utils import register_class, unregister_class
from .. materials.materials import (
    get_blend_filenames,
    load_materials)


# File and directory handling
def get_path():
    """returns addon path"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_addon_name():
    """returns file path name of calling file"""
    return os.path.basename(get_path())


def get_prefs():
    """returns MakeTile preferences"""
    return bpy.context.preferences.addons[get_addon_name()].preferences


'''
def reload_asset_libraries(library="ALL", default=None):
    """reloads passed in asset libraries"""
    if library == "ALL":
        unregister_assets()
        register_assets(reloading=True)
'''


def register_classes(classlist):
    for cls in classlist:
        register_class(cls)


def unregister_classes(classlist):
    for cls in classlist:
        unregister_class(cls)


def register_materials():
    print("Registering MakeTile Materials")
    addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    materials_path = os.path.join(addon_path, "assets", "materials")
    blend_filenames = get_blend_filenames(materials_path)
    load_materials(materials_path, blend_filenames)


#TODO: Stub
def unregister_materials():
    print("Unregistering MakeTile Materials")
