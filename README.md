# SDFGen
A robotics-focused addon for Blender that converts Blender files to SDF.<br>

## Installation  
1. **Download the addon:** [SDFGen addon](https://github.com/cole-bsmr/collidergen/blob/main/collidergen.py)<br>
2. Go to **Edit > Preferences > Add-ons** and click the downward facing arrow in the upper-right. Click **Install from disk...** from the dropdown.<br>
3. Select the `SDFGen.py` file. Activate it by checking the box next to it.<br>
4. Press **N** to open the **N-panel** where you can access the tool.
5. Note that after installing the addon Blender may attempt to aautomatically active the addon, however you may need to disable and enable the addon by unchecking and then checking the box next to it. 

# How to Use  

## Utilities  
The Utilities panel provides quick access to importers for common file types and tools to prepare imported meshes for applying collision objects.

### STL/FBX/OBJ/DAE Importers  
- These importers load common mesh file types. They are the same as Blender's default tools.<br>
- CAD formats like STEP are not natively supported.

### Clear Hierarchy / Reset Scale  
- Cleans up imported meshes by removing hierarchies and deleting empty objects.<br>
- Resets scale values to maintain accurate dimensions.<br>
- It’s recommended to use this tool on all imported geometry.

### Separate Parts  
- Identifies continuous geometry and separates it into distinct meshes.<br>
- Use this for better control over collision placement if your geometry isn’t already split into parts.

![Separate Parts Example](https://i.imgur.com/m6bmgMc.png)

### Separate by Material  
- Splits meshes based on their materials, useful for organizing the scene.

### Select Small Parts  
- Selects meshes below a certain volume, making it easier to remove insignificant parts and reduce polygon count.

## Create Panel

### Hierarchy Tab
Organize the Blender outliner to match the SDF structure.

#### Models
- Use this area to manage your models. Each model is a separate Blender scene and you can use this section to add, remove, and rename models. 

#### Create Link  
- Creates a link collection.  
  - Drag it into a model collection.<br>
  - A visual and collider collection will also be created within the link.<br>
  - Place visual objects in the visual collection. Generated collisions go into the collider collection.
#### Clone Link  
- Clones the active link collection.
#### Create Instance 
- This will create an instance of another model in your current model/scene.
### Colliders Tab
Create both simple and mesh-based collisions.

#### Options  

##### Show/Hide Colliders
- Toggle to show or hide collision objects.

##### Per Object  
- Applies operations to each object individually or to the whole selection.<br>
- When enabled, collisions are applied per object; otherwise, one collider fits the entire selection.

![Per Object Example](https://i.imgur.com/xhE0KGM.png)

##### Minimal Box  
- Aligns the box collider to the object's local rotation or fits it tightly.<br>
- Use this when the object’s rotation has been reset but needs proper alignment.

![Minimal Box Example](https://i.imgur.com/vTnr4ON.png)

- Credit to **iyadahmed** for the minimal-box script.<br>
  <https://gist.github.com/iyadahmed/512883896348a7e06f7a43f3ea8580af>

##### Collider Margin  
- Adjusts the global distance between the mesh surface and colliders.

#### Simple Colliders  
##### Box, Sphere, Cone, Plane  
- Creates a shape that fits the selected geometry.

##### Cylinder  
- Creates a cylinder aligned along the X, Y, or Z axis.<br>
  - Press **X**, **Y**, or **Z** to select the axis.<br>
  - Confirm with **Enter** or cancel with **Esc**.

##### Generate by Face  
- Creates box or cylinder collisions aligned to flat or cylindrical surfaces.<br>
  - Select a surface as the “end cap” for the shape, which extrudes from there.<br>
  - Adjust the extruded length if necessary.

#### Mesh Colliders  
- Generates a convex hull mesh with options to simplify it.

![Mesh Collider Example](https://i.imgur.com/IJpDfwR.png)

##### Simplify  
- Reduces the triangle count of the generated mesh.

##### Inflate  
- Inflates the mesh to fully cover the object when simplified.

#### Transform  
##### Scale Cage  
- Uses Blender’s **Scale Cage** tool to transform collider shapes.

##### Snap  
- Enables face snapping, useful for aligning colliders with surfaces.

##### Diameter  
- Adjusts the radius of cylinder collision shapes.

### Joints Tab
##### Show/Hide Joints
- Toggle to show or hide joints.
##### Joint Color
- Adjust the color of joint objects to be more visible

#### Create Joint
- Select the joint type from the dropdown, select an object, and press **Create Joint**.

## Properties  

### Joint Properties  
#### Parent and Child  
- Set parent-child relationships by selecting or dragging link collections.

#### Continuous  
- Available for revolute joints, allowing 360-degree rotation without limits.

#### Lower and Upper Limit  
- Sets joint limits.<br>
  - For revolute joints: degrees<br>
  - For prismatic joints: distance units

### Visual Properties  
#### Material  
- Select a material. Materials have densities used in inertial calculations.

#### Custom Density  
- Enable this to use a custom density.

#### Decimate  
- Reduces the polygon count of your object. Adjust the **Ratio** slider to control decimation.

### Link Properties  
#### Static  
- Choose whether a link is static or dynamic.<br>
- Inertial properties are generated only for dynamic links.

## Export  
Tools to export SDF files.

#### Mesh File Type  
- Choose a file type for visual meshes. Collision meshes are always exported as STL.

#### Mesh Files Path  
- Define the path prefix for mesh files in the SDF.

#### File Directory  
- Select the folder where SDF and generated mesh files will be saved.

#### Export  
- Press **Export** to save your SDF!

## Features to add
   -  Apply visual material when selecting a physics material
   -  More feedback when an error occurs
   -  Add more joint types
   -  Allow collider creation in edit mode with collliders fitting to vert/face/edge selection
   -  Add ability to export lights, camera, sensors, etc
   -  Add more properties for models, links, etc
   -  SDF file import
   -  Add the ability to run the scene in Gazebo immediately after export
   -  Improve the accuracy of the inertial values that are calculated
   -  Improve UI layout


## Version history
### SDFGen 1.0.2 
- Fixed issue with exporting mesh colliders.
- Models are no longer collections within scenes but are now the scenes themselves. 
- Reworked UI. Create panels now organized in tabs and placed visualization options within those tabs as well.
- Added some error reporting.
### SDFGen 1.0.1
 - Fixed issue with export path not always working.
