# MakeTile
A 3D printable dungeon tile creator addon for Blender 2.8x

A series of videos on how to use MakeTile can be found on my YouTube channel here https://www.youtube.com/channel/UC7TUNzEtli-sQRj5anS7DFA

Make sure you download the latest release by going to https://github.com/richeyrose/make-tile/releases and then downloading the latest MakeTile.zip file as this contains a .blend file with assets that are necessary for MakeTile to work.

You can back MakeTile on Kickstarter from 4th August! https://www.kickstarter.com/projects/modmodterrain/maketile-custom-dungeon-tile-creator

# Feature Roadmap
Features tagged **Community** will be available for download from this public repository.

Features tagged **Core** will be available to Kickstarter backers who have supported the core tier.

Features tagged **Plus** will be available to Kickstarter backers who have supported the plus tier.
## Phase 1
- [ ] Basic user documentation - Community
- [ ] Optimise existing materials - Community
- [ ] Implement pegs so tiles can be stacked - Community
- [ ] OpenLOCK I, L, O, T, X column tiles - Core

## Phase 2
- [ ] OpenLOCK roof and chimney pack 1 - Plus
- [ ] Static window, door and stair models - Core
- [ ] Basic version of asset manager - Core
- [ ] OpenLOCK compatible T and X wall tiles - Core
- [ ] Additional materials pack pt. 1 - Plus

## Phase 3
- [ ] Windows and doors generator - Plus
- [ ] OpenLOCK S-Walls pack - Plus
- [ ] Stairs generator - Plus
- [ ] Additional materials pack pt. 2 - Plus

## Phase 4
- [ ] OpenLOCK roof and chimney pack 2 - Plus
- [ ] OpenLOCK secondary and weird walls and floors pack - Plus
- [ ] OpenLOCK roof and chimney pack 3 - Plus

# FAQ

## Moving Tiles
## I can't move my tile! Help!
By default you can only move, rotate, or scale the base part of a tile to which everything else is parented. The reason for this is that a tile in MakeTile is actually a Blender collection made up of multiple objects and if the parts get out of alignment MakeTile will no longer work properly.

If you do find yourself ever needing to move an individual part of a tile go to the **Item** tab in the right hand menu and click on the padlock icons to unlock the axis.

![Image of transform panel](/docs/images/TransformPanel.png)

## Materials
## I've added a material and some of the tiles look like this. How do I fix this?
![Image of material rotation error](/docs/images/MaterialRotationError.png)

This happens because of the way a tile has been rotated. To fix this make sure one of the tiles with that material on is selected and go to the **Materials** panel in the MakeTile menu. Select the material that is showing incorrectly and then come down to the **Material Mapping** panel. Select the eye dropper in the **Reference Object** box and select an object in the scene that has not been rotated. If you need to add an object to do this press **shift + a** or click on **Add** in the top left of the main window and add an empty.

The material should now display correctly. You can also change the material mapping method to **Triplanar** if your tile is a floor tile, or a straight wall tile, or a corner tile with a 90 degree angle and it should display correctly.

## Importing other objects
### I've imported something and its huge! How do I rescale it?
If you've imported something that is sized for 3D printing that you want to add to your tile then select your object and in the **Object Coverter** panel in the MakeTile menu select the correct Tile Units and click on **Rescale Object**. If you are creating OpenLOCK tiles this should be inches.

If you want to rescale something manually select the object and press **s** on the keyboard or select the object and then the scale widget icon and use that.

![Image of Scale Widget](/docs/images/ScaleIcon.png)


### I want to add a prop to my tile and then export it for printing. How do I do this?
Move the prop so it is on your tile, ensuring that there is no gap. Select your prop and then the tile and then in the **Object Converter** panel in the MakeTile menu click **Add Selected to Tile** If you have **Voxelise** selected when you export it MakeTile will fuse the prop to your tile and create a single mesh.

### How do I use MakeTile's material system with an imported object?
Select the object and then click **Convert to MakeTile Object** in the **Object Converter** panel in the MakeTile menu. For more details check out these two videos:

* https://youtu.be/h-Ayb_r4dls
* https://www.youtube.com/watch?v=PL5DsjluTqU&t=263s

## Exporting
### Why is my tile tiny when I export it for printing?
Rather than exporting your tile using the main Blender menu you should use the exporter built into MakeTile. You can find this at the bottom of the MakeTile menu.
This will rescale your tile to inches or cm depending on what is selected in the **Units** dropdown.

### How do I export Random variants?
You can export random variants of a tile using the MakeTile export menu by selecting the **Randomise** check box and entering the number of variants you want.

### I've turned off Randomise and now when I export a tile it has no material. How do I fix this?
Make sure you have clicked **Make3D** before exporting your tile if you just want to create a single tile without randomising it.

### I've exported a tile and the file is huge. How do I fix this?
Checking **Voxelise** will voxelise your tile on export and then simplify it, reducing the final poly count. You can find the voxel settings in the **Voxelise Settings** panel in the MakeTile menu. Increasing the **Voxel Size** will reduce the amount of detail picked up. Increasing the **Adaptivity** will increase the amount of post voxelisation simplification.

### After I've exported my mesh it's lost some detail. How do I fix this?
You can change the size of voxels and amount of simplification in the **Voxelise Settings** panel in the MakeTile menu. Decreasing the **Voxel Size** will pick up more detail. Decreasing the **Adaptivity** wil decrease the amount of post voxelisation simplification. You can also turn off Voxelisation altogether but be warned the file size will be huge.

### How do I change the default export path that MakeTile uses?
Go to **Edit** > **Preferences** > **Add-ons** > **MakeTile** and choose the new default export path.

### I've created a building and now I want to export it as a single mesh rather than individual tiles. How can I do this?
Check out this video on how to do this: https://youtu.be/x95RjKsU4Qg

## Licensing and copyright info
MakeTile is licensed under the GNU GPLv3 http://www.gnu.org/licenses/

All objects, materials and images bundled with MakeTile in the form of a .blend file are copyright ModMod Terrain Ltd under the [Creative Commons-Attribution-Non-Commercial](https://creativecommons.org/licenses/by-nc/4.0/) license unless otherwise noted.

Current exceptions are any meshes required for the generation of OpenLOCK tiles which are copyright Printablescenery under the [Creative Commons-Attribution-Non-Commercial](https://creativecommons.org/licenses/by-nc/4.0/) license

If you would like to use the materials or meshes bundled with MakeTile for commercial purposes and have backed MakeTile through Kickstarter please [contact me](https://github.com/richeyrose/make-tile/issues) by raising an issue for a free commercial license.

If you would like to produce OpenLOCK compatible tiles for commercial purposes please contact [Printablescenery]( https://www.printablescenery.com) for a free commercial license