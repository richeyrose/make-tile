"""Contains elements used in the creation of panels for the tile generators."""

def scene_tile_panel_header(scene_props, layout, blueprints, tile_type):
    """Header for N menu tile generator panels.

    Args:
        scene_props (mt_scene_props): mt scene properties
        layout (bpy.types.UILayout): Area to draw in
        blueprints (list): list of blueprint names
        tile_type (str): str in [WALL, FLOOR, ROOF]
    """
    layout.label(text="Blueprints")
    for blueprint in blueprints:
        layout.prop(scene_props, blueprint)

    if 'base_blueprint' in blueprints and 'OPENLOCK' in scene_props.base_blueprint:
        layout.prop(scene_props, 'base_socket_type')
        layout.prop(scene_props, 'generate_suppports')

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
    """Footer for the N menu tile generator panels.

    Args:
        scene_props (mt_scene_props): Scene properties
        layout (bpy.types.UILayout): Area to draw in
    """
    layout.label(text="Subdivision Density")
    layout.prop(scene_props, 'subdivision_density', text="")

    layout.label(text="UV Island Margin")
    layout.prop(scene_props, 'UV_island_margin', text="")

    layout.operator('scene.reset_tile_defaults')

def scene_straight_tiles_panel(scene_props, layout):
    """Shared content for the N menu straight tile generator panels.

    Args:
        scene_props (mt_scene_props): MakeTile scene properties
        layout (bpy.type.UILayout): Area to draw in.
    """
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

def scene_curved_tiles_panel(scene_props, layout):
    """Shared content for the N menu curved tile generator panels.

    Args:
        scene_props (mt_scene_props): MakeTile scene properties
        layout (bpy.types.UILayout): Area to draw in.
    """
    layout.label(text="Tile Properties")
    layout.prop(scene_props, 'tile_z', text="Height")
    layout.prop(scene_props, 'base_radius', text="Radius")
    layout.prop(scene_props, 'degrees_of_arc')
    layout.prop(scene_props, 'base_socket_side', text="Socket Side")
    layout.prop(scene_props, 'curve_texture', text="Curve Texture")


    layout.label(text="Core Size")
    layout.prop(scene_props, 'tile_y', text="Width")

    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(scene_props, 'y_proportionate_scale', text="Width")
    row.prop(scene_props, 'z_proportionate_scale', text="Height")

    layout.label(text="Base Size")
    layout.prop(scene_props, 'base_y', text="Width")
    layout.prop(scene_props, 'base_z', text="Height")

def scene_L_tiles_panel(scene_props, layout):
    """Shared content for the N menu L tiles generator panels.

    Args:
        scene_props (mt_scene_props): MakeTile scene properties
        layout (bpy.type.UILayout): Area to draw in.
    """
    layout.label(text="Tile Properties")
    layout.prop(scene_props, 'leg_1_len')
    layout.prop(scene_props, 'leg_2_len')
    layout.prop(scene_props, 'angle')
    layout.prop(scene_props, 'tile_z', text="Height")

    layout.label(text="Core Properties")
    layout.prop(scene_props, 'tile_y', text="Width")

    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(scene_props, 'z_proportionate_scale', text="Height")
    row.prop(scene_props, 'y_proportionate_scale', text="Width")

    layout.label(text="Base Properties")
    layout.prop(scene_props, "base_z", text="Height")
    layout.prop(scene_props, "base_y", text="Width")

def redo_tile_panel_header(self, layout, blueprints, tile_type):
    """Header for the tile generator's redo panels

    Args:
        layout (bpy.types.UILayout): Are to draw in
        blueprints (list[str]): list of blueprints
        tile_type (str): String in [WALL, FLOOR, ROOF]
    """
    layout.label(text="Blueprints")
    for blueprint in blueprints:
        layout.prop(self, blueprint)

    if 'base_blueprint' in blueprints and 'OPENLOCK' in self.base_blueprint:
        layout.prop(self, 'base_socket_type')
        layout.prop(scene_props, 'generate_suppports')

    layout.label(text='Materials')
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
    """Footer for tile generator's redo panel

    Args:
        layout (bpy.types.UILayout): Area to draw in
    """
    layout.label(text="UV Island Margin")
    layout.prop(self, 'UV_island_margin', text="")

def redo_straight_tiles_panel(self, layout):
    """Shared content for redo panel for straight tiles.

    Args:
        layout (bpy.types.UILayout): Area to draw in.
    """
    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(self, 'x_proportionate_scale')
    row.prop(self, 'y_proportionate_scale')
    row.prop(self, 'z_proportionate_scale')

    layout.label(text="Base Sizse")
    row = layout.row()
    row.prop(self, 'base_x')
    row.prop(self, 'base_y')
    row.prop(self, 'base_z')

def redo_curved_tiles_panel(self, layout):
    """Shared content for redo panel for curved tiles.

    Args:
    layout (bpy.types.UILayout): Area to draw in.
    """
    if self.base_blueprint not in ('PLAIN', 'NONE'):
        layout.prop(self, 'base_socket_type')
        layout.prop(scene_props, 'generate_suppports')

    layout.label(text="Tile Properties")
    layout.prop(self, 'tile_z', text="Height")
    layout.prop(self, 'base_radius', text="Radius")
    layout.prop(self, 'degrees_of_arc')
    layout.prop(self, 'base_socket_side', text="Socket Side")
    layout.prop(self, 'curve_texture', text="Curve Texture")

    layout.label(text="Core Size")
    layout.prop(self, 'tile_y', text="Width")

    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(self, 'y_proportionate_scale', text="Width")
    row.prop(self, 'z_proportionate_scale', text="Height")

    layout.label(text="Base Size")
    layout.prop(self, 'base_y', text="Width")
    layout.prop(self, 'base_z', text="Height")

    if self.base_blueprint in ('OPENLOCK_S_WALL', 'PLAIN_S_WALL'):
        layout.label(text="Floor Thickness")
        layout.prop(self, 'floor_thickness', text="")

        layout.label(text="Wall Position")
        layout.prop(self, 'wall_position', text="")


def redo_L_tiles_panel(self, layout):
    """Shared content for redo panel for L Tiles.

    Args:
        layout (bpy.types.UILayout): Area to draw in.
    """
    layout.label(text="Tile Properties")
    layout.prop(self, 'leg_1_len')
    layout.prop(self, 'leg_2_len')
    layout.prop(self, 'angle')
    layout.prop(self, 'tile_z', text="Height")

    layout.label(text="Core Properties")
    layout.prop(self, 'tile_y', text="Width")

    layout.label(text="Sync Proportions")
    row = layout.row()
    row.prop(self, 'z_proportionate_scale', text="Height")
    row.prop(self, 'y_proportionate_scale', text="Width")

    layout.label(text="Base Properties")
    layout.prop(self, "base_z", text="Height")
    layout.prop(self, "base_y", text="Width")