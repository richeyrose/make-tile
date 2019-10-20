import os
import bpy

# File and directory handling
def get_path():
    """returns file path of calling file"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def get_addon_name():
    """returns file path name of calling file"""
    return os.path.basename(get_path())

def get_prefs():
    """returns MakeTile preferences"""
    return bpy.context.preferences.addons[get_addon_name()].preferences

def reload_asset_libraries(library="ALL", default=None):
    """reloads passed in asset libraries"""
    if library == "ALL":
        unregister_assets()
        register_assets(reloading=True)

assets = {}

#TODO: stub
def register_assets(library="ALL", default=None, reloading=False):
    assets_path = get_prefs().assets_path

#TODO: stub
def unregister_assets(library="ALL"):
    print("unregistering assets")
