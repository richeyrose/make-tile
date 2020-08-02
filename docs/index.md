# Welcome to MakeTile

MakeTile is a custom dungeon tile creator for [Blender](https://www.blender.org/) - the free, open source 3D modelling program. Using MakeTile you can simply and easily create 3D printable tiles of the exact dimensions you need, add procedurally generated, customizable materials to make them look like stone, wood, brick etc. hit the Make3D button and export them for printing.

You can download the [prototype](https://github.com/richeyrose/make-tile/releases) version of MakeTile today from GitHub. (Be warned, here be bugs!).

If you back MakeTile on [Kickstarter](https://www.kickstarter.com/projects/modmodterrain/maketile-custom-dungeon-tile-creator) you will get access to additional tile types and materials.

## Installing MakeTile
1. MakeTile is an add-on for Blender. First [download](https://www.blender.org/download/) the latest build of Blender and install it. If you've not used Blender before I *strongly* advise that you first take a look at the first five Blender fundamentals [videos](https://www.youtube.com/playlist?list=PLa1F2ddGya_-UvuAqHAksYnB0qL9yWDO6) on the official Blender YouTube channel. These will teach you the basics of viewport navigation, the Blender interface and how to add and delete objects. It should take you no more than 30 minutes.
2. Download the latest build of MakeTile. If you are downloading the prototype or community version you can download the latest version from [here](https://github.com/richeyrose/make-tile/releases). If you have supported MakeTile on Kickstarter you will have been emailed a link to download your supported version. Click on the **Assets** drop down and download the **MakeTile.zip** file. This contains several materials and meshes that are needed for MakeTile to work which aren't included in the source. **Do not unzip this file!!!** Blender uses the .zip file directly to install add-ons and if you unzip it the installation will silently fail.
3. Launch Blender and click anywhere in 3D space to get rid of the splash screen.
4. In the top menu go to **Edit** > **Preferences** > **Add-ons** > **Install...** Select the .zip file you have just downloaded and click on **Install Add-on.** After a few seconds MakeTile should appear. If it doesn't use the search box in the top right. Click on the box to the left of MakeTile to activate it. Close the preferences window.

## Basics
### Quickstart guide
MakeTile lives in its own tab in the right hand menu. Press **N** to show or hide this menu and click on the MakeTile tab to access its options.

![Right hand menu](/docs/images/NMenu.png)

1. To create your first tile select the default cube by left clicking and press **delete**. In the right hand menu leave the defaults as they are and click on the **MakeTile** button. Congratulations, you have just made your first tile!
2. Currently your tile will be blank, so in the **Display Settings** panel click on **Create lighting setup.** Blender should think for a second or two and now your tile should be in glorious 3D!

    You will notice that as you rotate around the scene the viewport doesn't update instantaneously. This is because we are currently in Cycles mode, which is Blender's none real time renderer, which we need to use to preview our tiles in 3D. When we're in Cycles mode the 3D displacement is being calculated in the shader and it is not yet "real" geometry.

    ![Cycles Tile](/docs/images/CyclesTile.png)

    To switch to Blender's realtime renderer, Eevee, either select **Eevee** in the drop down menu in the **Display Settings** panel or click on the **Material Preview** icon in the horizontal menu bar above the MakeTile menu.

    ![Material Preview Button](/docs/images/MaterialPreviewButton.png)

    You should still be able to see the material on your tile, but it should now be a flat texture rather than being 3D and the viewport should be updating smoothly now.

3. To make our tile truly 3D, select the main part of the tile and click on the **Make 3D** button. Blender will think for a second or two and then the tile will appear in 3D. What you are seeing now is real geometry that we can export and print.
4. Hover your mouse over the MakeTile menu and scroll with the scroll wheel down to the bottom where you'll find the **Export Panel**. Expand the panel, make sure your tile is selected, and click on the **Export Tile** button. Blender will now pause for a few moments while MakeTile does its magic before exporting your tile to the folder in the **Export Path** box. By default this will be in your user\MakeTile directory. You can change this path before exporting your tile by clicking on the folder icon, and you can change the default path in the MakeTile add-on preferences. Your tile is now ready to slice and print!
### Moving and deleting tiles
Each tile created by MakeTile is actually a collection of objects which need to move together in order for MakeTile to function correctly. Because of this you can only move the base of a tile and everything else will move with it.

If you want to delete a tile you should use the **Delete Tiles** button in the MakeTile menu rather than pressing delete. This will delete all objects that make up that tile. You can also delete a tile by going to the outliner on the right hand side, selecting the tile collection, right clicking, and selecting **Delete Hierarchy**. This is useful for if you've accidentally deleted part of a tile.

![Outliner](/docs/images/Outliner.png)