# Menus for EnumProperty's

collection_types = [
    ("TILE", "Tile", ""),
    ("ARCH_ELEMENT", "Architectural Element", ""),  # e.g. a doorway or window that should be added to a tile rather than printed on its own
    ("BUILDING", "Building", ""),  # a building type prefab consisting of multiple tiles to be printed separately
    ("OTHER", "Other", "")]

units = [
    ("INCHES", "Inches", "", 1),
    ("CM", "Centimeters", "", 2)
]

curve_types = [
    ("POS", "Positive", "", 1),
    ("NEG", "Negative", "", 2),
]

tile_blueprints = [
    ("PLAIN", "Plain", "", 1),
    ("OPENLOCK", "OpenLOCK", "", 2),
    ("CUSTOM", "Custom", "", 3),
]

tile_main_systems = [
    ("OPENLOCK", "OpenLOCK", "", 1),
    ("PLAIN", "Plain", "", 2),
    ("NONE", "None", "", 3)
]

base_systems = [
    ("OPENLOCK", "OpenLOCK", "", 1),
    ("PLAIN", "Plain", "", 2),
    ("NONE", "None", "", 3)
]

tile_types = [
    ("STRAIGHT_WALL", "Straight Wall", "", 1),
    ("CURVED_WALL", "Curved Wall", "", 2),
    ("L_WALL", "Corner Wall", "", 3),
    ("U_WALL", "U Wall", "", 4),
    ("RECTANGULAR_FLOOR", "Rectangular Floor", "", 5),
    ("TRIANGULAR_FLOOR", "Triangular Floor", "", 6),
    ("CURVED_FLOOR", "Curved Floor", "", 7),
    ("L_FLOOR", "Corner Floor", "", 8),
    ("STRAIGHT_FLOOR", "Straight Floor", "", 9),
    ("SEMI_CIRC_FLOOR", "Semi Circular Floor", "", 10)
    #("CONNECTING_COLUMN", "Connecting Column", "", 11)
]

# TODO: Get rid of difference etc. from here and always use boolean_types
geometry_types = [
    ("NONE", "None", ""),
    ("BASE", "Base", ""),
    ("CORE", "Core", ""),
    # ("PREVIEW", "Preview", ""),
    # ("DISPLACEMENT", "Displacement", ""),
    ("DIFFERENCE", "Difference", ""),
    ("UNION", "Union", ""),
    ("PROP", "Prop", ""),
    ("GREEBLE", "Greeble", ""),
    ("TRIMMER", "Trimmer", ""),
    ("EMPTY", "Empty", ""),
    ("VOXELISED", "Voxelised", ""),
    ("FLATTENED", "Flattened", ""),
    ("ADDITIONAL", "Additional", "")
]

boolean_types = [
    ("UNION", "Union", ""),
    ("DIFFERENCE", "Difference", ""),
    ("INTERSECT", "Intersect", "")]

base_socket_side = [
    ("INNER", "Inner", "", 1),
    ("OUTER", "Outer", "", 2)
]

view_mode = [
    ("CYCLES", "Cycles", ""),
    ("EEVEE", "Eevee", ""),
    ("SOLID", "Solid", "")
]

material_mapping = [
    ("WRAP_AROUND", "Wrap around", "", 1),
    ("TRIPLANAR", "Triplanar", "", 2),
    ("OBJECT", "Object", "", 3),
    ("GENERATED", "Generated", "", 4),
    ("UV", "UV", "", 5)
]

openlock_column_types = [
    ("I", "I Column", "", 1),
    ("L", "L Column", "", 2),
    ("O", "O Column", "", 3),
    ("T", "T Column", "", 4),
    ("X", "X Column", "", 5)
]

column_socket_style = [
    ("FLAT", "Flat", "", 1),
    ("TEXTURED", "Textured", "", 2)
]
