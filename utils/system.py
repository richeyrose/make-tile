# from DECALmachine #

import os
import bpy

def abspath(path):
    return os.path.abspath(bpy.path.abspath(path))

def makedir(pathstring):
    if not os.path.exists(pathstring):
        os.makedirs(pathstring)
    return pathstring