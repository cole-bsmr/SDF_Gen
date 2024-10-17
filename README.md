# ColliderGen
A robotics focused addon for Blender that creates collision geometry and SDF files.

For a demonstration of how to use this tool, you can take a look at this video of the Gazebo community meeting.
https://vimeo.com/908361057#t=36m0s

## Installation
 - Download the addon: **[ColliderGen addon](https://github.com/cole-bsmr/collidergen/blob/main/collidergen.py)**
 - Go to Edit > Preferences > Addons then click the “Install” button in the upper right. Select the collidergen.py file that you downloaded. Collider Gen will now appear in your list of addons and you can activate by checking the box next to it.
 - After activating you can press the "N" key to open up the "N-panel" which allows you to access the tool.

# How to use

## Utilities
The utilities panel allows you to quickly access importers for commonly used file types as well as prepare the imported meshes for applying collision objects.
#### STL/FBX/OBJ/DAE Importers
 - These simply give you access to importers for commonly used mesh file types. These are the same import tools used in default Blender. Note that support for importing CAD file formats like STEP are not natively support
#### Clear Hierarchy/Reset Scale
 - This tool performs some basic functions to clean up the imported meshes and ensures they work correctly with the tools that generate SDF elements like joints and colliders. It first removes objects from any imported hierarchy and deletes the empty objects. It then resets all scale values which is important for getting accurate dimensions of objects. It is highly recommended that this tool be used on all imported geometry.
#### Separate Parts
 - This tool identifies continuous geometry and separates those into separate meshes. This allows the user to have finer control over what collisions are placed where. If your imported geometry is already split into parts it’s not necessary to run this tool.
![](https://i.imgur.com/m6bmgMc.png)
#### Separate by Material
 - This tool will separate your meshes by material. This can be useful when settings up materials in your scene.
#### Select small parts
 - This tool will select all meshes under a certain volume. This is useful for deleting parts that are visually insignificant in order to reduce polygon count.

## Visibility
The visibility panel allows for turning on and off the visbility of certain elements to make the scene easier to read. Here you can also change the color of the joint visuals as they are black by default making them difficult to see. 

## Hierarchy
The hierarchy panel is where you can set up your outliner in Blender to match the hierarchy you would see in SDF. 
#### Create Model
 - Creates a model collection in the outliner
#### Create Link
 - Creates a link collection in the outliner. Drag this into a model collection. A visual and collider collection will also be automatically created within the link collection. Place your visuals in the visual link. When creating collisions on these objects those collisions will automatically be palced within the colliders colelction.
#### Clone Link
#### Create Include

## Generate Colliders
This panel is for creating collisions. Both simple shape collisions and mesh collisions can be created. 

### Options
The create options panel contains settings you can adjust to change the way the tools in the “Generate Colliders” panel behave.
#### Per Object
 - This option determines whether an operation is applied to the selected objects as a whole or to each object individually. When toggled on the tool will loop through each object and apply a collision to each object in that selection. When toggled off the tool will create one collider that fits the entire selection of objects. This option only applies to the “Box” and “Sphere” tools in the “Create” interface.
![](https://i.imgur.com/xhE0KGM.png)
#### Minimal Box
 - This option determines whether a created collider box is aligned to the object’s local rotation or whether it is fit to the object in a way that creates the tightest fitting collision. When toggled off the box collider will use the object’s local rotation to align itself. When toggled on the box collider will be fit to the object in the way that creates the tightest fitting box.
![](https://i.imgur.com/vTnr4ON.png)

 - This tool is mainly used for when an object is box-like and at an angle but its rotational information has been reset so that instead of creating a box that aligns to the geometry it is being aligned to the world. The “Minimal Box” setting will allow the correct alignment of box collisions to these types of geometries.
 - Credit to "iyadahmed" for allowing me to use his fantastic minimal-box script for Blender which can be found here https://gist.github.com/iyadahmed/512883896348a7e06f7a43f3ea8580af
#### Collider Margin
 - Adjust this value to increase the distance between the surface of the mesh and the colliders. This is a global value that will affect all colliders.

### Simple Colliders
#### Box, Sphere, Cone, Plane
 - These tools create a shape that fits around the selected geometry.
#### Cylinder
 - This tool creates a cylinder shape that fits around the selected geometry. After selecting this tool you’ll be required to select an axis. Pressing the the X, Y, or Z keys will create a cylinder object that aligns with that objects local X, Y, or Z axis. After choosing the axis that looks appropriate you can confirm your selection with the ENTER key or hit ESC to cancel the operation.
#### Generate by Face
 - This tool is a more advanced option for creating collision shapes that allows you to create box and cylinder collision shapes around cylindrical and boxy features even if they aren’t separate parts.
 - To use this tool select an object and then press the “Generate by Face” button. You can then select a flat surface of the object. This surface will be the “end cap” of your collision shape. After confirming your surface the collision object will be extruded from that surface. The length of this extruded shape is determined automatically but may need to be adjusted after the shape is generated.

### Mesh Colliders
 - This tool creates a collision mesh as opposed to a simple shape. It creates a convex hull mesh that can then be simplified. Simply select an object and press the button to create the mesh. You will then see two new tools appear under the button.
![](https://i.imgur.com/IJpDfwR.png)
 - The Simplify and Inflate tools will appear any time a mesh collider is selected and these values can be adjusted at any time as long as the modifiers have not been applied.
#### Simplify
 - This tool allows you to dynamically adjust the triangle count of the generated mesh.
#### Inflate
 - As you lower the triangle count and the coarseness of the mesh increases you will notice that parts of the mesh will begin to extend outside the geometry of the collider. Use this tool to inflate the collision mesh until it fully encompasses the object.

### Transform
#### Scale Cage
 - This tool simply selects Blender’s built-in “Scale Cage” tool which is ideal for transforming collider shapes.
#### Snap
 - This tool turns on snapping and sets the snapping settings to snap to face. These settings are ideal when using “Scale Cage” to move collision geometry to the surfaces of its associated object.
#### Diameter
 - This tool will only be visible on when a cylinder collision shape is selected. It allows you to adjust the radius of the collision shape.

## Generate Joints
This panel is for generating joints. Choose your desired joint type from the dropdown, select an object, then press the "Create Joint" button.

## Properties
This panel will display properties for the selected item. 
### Joint Properties
#### Parent and Child
 - Click and select a link collection or drag and drop a link collection from the outliner to the space.
#### Continuous
 - This will only appear if a revolute joint is selected. Check this if your joint does not have an upper and lower limit but instead rotates freely in 360 degrees.
#### Lower and Upper Limit
 - This will appear on joints that use limits. For revolute joints this will be in degrees and for prismatic joints it will be in distance.

### Visual Properties
#### Material
 - Choose your material. These have a density associated with them that will be used for inertial calculations.
#### Custom Density
 - Check this if you need a density that isn't in the listed materials
#### Decimate
 - This tool will allow you to reduce the polygon count of your object. Adjust the "Rario" slide to control the amount of decimation.

### Link Properties
#### Static
 - Choose whether your link is static or dynamic. Inertial properties will only be generated for dynamic links. 
 
## Export
This interface contains the tools needed to export your SDF. 
#### Mesh File Type
 - Choose your file type from the dropdown. This will only affect visual meshes. Collision meshes are always exported in STL format.
#### Mesh Files Path
 - Here you can define a path that will preceed the mesh files in the SDF.
#### File directory
 - Here you can select the folder in which to save the SDF files as well as any mesh files that were generated.
#### Export
 - Press this button to export your SDF!
