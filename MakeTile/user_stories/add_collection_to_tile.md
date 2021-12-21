## Pathway 1

Doorway collection already in scene.

### Collections in Scene:

tile_collection

doorway_collection


### User Story
Bob wants to add a doorway to a tile. He drags the *doorway_collection* onto the *tile_collection* and positions it correctly. He makes sure that the tile has been made 3d and that the doorway has also.
He selects an object in the *doorway_collection* and then selects an object in the *tile_collection*. In the MakeTile menu he clicks the **Add collection to tile** Operator button.

### MakeTile actions
Any objects in the doorway_collection with geometry_type 'DIFFERENCE' are added as booleans to any objects with geometry type "CORE" and optionally if the "affects_base" flag is set to the base.

Any objects in the doorway_collection with geometry_type 'UNION' are added to the tile_collection collection. This means that they will be included on export.

all objects in the doorway_collection are parented to the tile_collection object with geometry type 'BASE'

