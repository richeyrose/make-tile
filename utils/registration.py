import os
import bpy

# File and directory handling
def get_path():
    """returns file path of calling file"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def get_path_name():
    """returns file path name of calling file"""
    return os.path.basename(get_path())


