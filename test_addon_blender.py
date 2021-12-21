from pathlib import Path
import sys
# to run type python test_addon_blender.py at the command line

try:
    import blender_addon_tester as BAT
except Exception as e:
    print(e)
    sys.exit(1)

def main():
    addon = "MakeTile"
    blender_rev = "3.0.0"

    try:
        exit_val = BAT.test_blender_addon(addon_path=addon, blender_revision=blender_rev)
    except Exception as e:
        print(e)
        exit_val = 1
    sys.exit(exit_val)

main()