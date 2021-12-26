import bpy

def scene_tile_panel_header(scene_props, layout, blueprints, tile_type):
    layout.label(text="Blueprints")
    for blueprint in blueprints:
        layout.prop(scene_props, blueprint)

    if 'base_blueprint' in blueprints and scene_props.base_blueprint not in ('PLAIN', 'NONE'):
        layout.prop(scene_props, 'base_socket_type')

    layout.label(text="Materials")
    if tile_type == 'FLOOR':
        layout.prop(scene_props, 'floor_material')

    if tile_type == 'WALL':
        layout.prop(scene_props, 'wall_material')

        if scene_props.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.prop(scene_props, 'floor_material')

            layout.label(text="Floor Thickness")
            layout.prop(scene_props, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(scene_props, 'wall_position', text="")

def scene_tile_panel_footer(scene_props, layout):
    layout.label(text="Subdivision Density")
    layout.prop(scene_props, 'subdivision_density', text="")

    layout.label(text="UV Island Margin")
    layout.prop(scene_props, 'UV_island_margin', text="")

    layout.operator('scene.reset_tile_defaults')

def scene_straight_tiles_panel(scene_props, layout):
    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(scene_props, 'x_proportionate_scale')
    row.prop(scene_props, 'y_proportionate_scale')
    row.prop(scene_props, 'z_proportionate_scale')

    layout.label(text="Base Size")
    row = layout.row()
    row.prop(scene_props, 'base_x')
    row.prop(scene_props, 'base_y')
    row.prop(scene_props, 'base_z')

def redo_tile_panel_header(self, layout, blueprints, tile_type):
    layout.label(text="Blueprints")
    for blueprint in blueprints:
        layout.prop(self, blueprint)

    if 'base_blueprint' in blueprints and self.base_blueprint not in ('PLAIN', 'NONE'):
        layout.prop(self, 'base_socket_type')

    layout.label(text='MATERIALS')
    if tile_type == 'FLOOR':
        layout.prop(self, 'floor_material')

    if tile_type == 'WALL':
        layout.prop(self, 'wall_material')
        if self.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
            layout.prop(self, 'floor_material')

            layout.label(text="Floor Thickness")
            layout.prop(self, 'floor_thickness', text="")

            layout.label(text="Wall Position")
            layout.prop(self, 'wall_position', text="")

def redo_tile_panel_footer(self, layout):
    layout.label(text="UV Island Margin")
    layout.prop(self, 'UV_island_margin', text="")

def redo_straight_tiles_panel(self, layout):
    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(self, 'x_proportionate_scale')
    row.prop(self, 'y_proportionate_scale')
    row.prop(self, 'z_proportionate_scale')

    layout.label(text="Base Size")
    row = layout.row()
    row.prop(self, 'base_x')
    row.prop(self, 'base_y')
    row.prop(self, 'base_z')