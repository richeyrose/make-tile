import cProfile, pstats, io
from pstats import SortKey
import bpy



def profile_operator(op_call):
    #op_call = 'bpy.ops.object.make_straight_wall(invoked=False, executed=True, base_updated=True, refresh=True, auto_refresh=True, reset_defaults=False, defaults_upated=False, main_part_blueprint=\'OPENLOCK\', base_blueprint=\'OPENLOCK\', x_proportionate_scale=True, y_proportionate_scale=False, z_proportionate_scale=False, tile_x=2.515, tile_y=0.32, tile_z=2, base_x=2.515, base_y=0.5, base_z=0.2755, tile_size=(0, 0, 0), base_size=(0, 0, 0), collection_type=\'TILE\', tile_name="straight_wall.009", is_mt_collection=True, converter_material=\'Basic Stone 1\', export_subdivs=3, subdivision_density=\'MEDIUM\', UV_island_margin=0.012, texture_margin=0.001, tile_units=\'INCHES\', wall_position=\'CENTER\', floor_thickness=0.0245, floor_material=\'Floor Tiles\', wall_material=\'Basic Stone 1\')'
    profile = cProfile.Profile()
    profile.enable()
    bpy.ops.object.make_straight_wall(invoked=False, executed=True, base_updated=True, refresh=True, auto_refresh=True, reset_defaults=False, defaults_upated=False, main_part_blueprint='OPENLOCK', base_blueprint='OPENLOCK', x_proportionate_scale=True, y_proportionate_scale=False, z_proportionate_scale=False, tile_x=2.015, tile_y=0.32, tile_z=2, base_x=2.015, base_y=0.5, base_z=0.2755, tile_size=(0, 0, 0), base_size=(0, 0, 0), collection_type='TILE', tile_name="straight_wall.013", is_mt_collection=True, converter_material='Basic Stone 1', export_subdivs=3, subdivision_density='MEDIUM', UV_island_margin=0.012, texture_margin=0.001, tile_units='INCHES', wall_position='CENTER', floor_thickness=0.0245, floor_material='Floor Tiles', wall_material='Basic Stone 1')
    profile.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(profile, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

