# SDF_Gen Guide [WIP]

## Workspaces
SDF_Gen is organized into **“workspaces”**. Each space is focused on a specific step in the SDF creation process. Accessing each workspace is done through a row of tabs at the top of the addon UI.

---

## Utilities
The `Utilities` tab is for processing imported meshes to make them suitable for working with in SDF Gen.

### Clean Mesh
`Clean Mesh` attempts to repair any parts of the mesh that may have issues, such as incorrect scale transforms. It also removes any hierarchy or parenting which can cause issues with collision generation.

### Separation Tools
The `Separation Tools` allow the mesh to be split into smaller parts. This allows for parts to be organized into the appropriate links and for more refined collision generation.

### Select Small Parts
`Select Small Parts` is used to select parts under a certain volume. This is useful for removing geometry that may not be important but can potentially add a lot of polygons, such as small bolts and screws.

---

## Links
The `Links` workspace focuses on creating the basic structure of the SDF. This includes creating and naming models, links, visuals, etc.

### Models
The `Models` tab uses Blender’s “scene” system. One Blender file can store multiple models. On export, each model will be exported as a separate SDF file. In this section, models can be added, removed, or renamed.

### Collections
The `Collections` section is for creating collections that will be used to organize the mesh objects into categories.
* Clicking **`Create Link`** will create a collection that also houses a `visual` and `collision` collection.
* Store your visual meshes in these `visual` collections.
* Collision geometry will be stored in the `collision` collections when creating them in the `Colliders` workspace.

### Links List
The `Links List` will show you an overview of your created links.

---

## Colliders
The `Colliders` tab is for the creation of collision primitives and collision geometry.

### Primitive Colliders
Create primitive colliders that will fit around a selected visual object. When creating a primitive collider, use the operation panel in the lower-left of the viewport to affect how the primitive is applied.

#### Operation Panel
* **`Minimal Box`**: Fits the box as tightly as possible to the object, ignoring the object's origin orientation. This is particularly useful for objects that are at an angle that’s not reflected in the object’s rotation transform.
* **`Per Object`**: Creates a collider for each of the selected objects, as opposed to one single collider that fits around the entire selection.
* **`Axis Set`**: Changes the orientation of objects such as cylinders and planes.

### Mesh Collider
Creates a convex hull mesh collider. This method is less efficient but provides higher accuracy. Use the operation panel to:
* Reduce the resolution of the convex hull mesh using the **`Mesh Resolution`** slider.
* Adjust the **`Mesh Margin`** slider to ensure all parts of the visual object are contained within the collider as mesh resolution is lowered.

### Transform
Colliders will often need to be adjusted to properly fit the underlying visual objects. Use these tools to manually adjust the colliders.
* The **`Scale Cage`** tool can be used to push and pull the boundaries of the collision primitive.
* The **`Face Snap`** setting allows those boundaries to be snapped to the surface of the underlying visual object.
* **`Collider Margin`** is a global setting used to create a margin between the visual object and the collision. This applies to all colliders in the scene.

> **💡 Tip:**
> For primitive colliders, select multiple objects and turn off `Per Object` to create colliders that cover large parts of the object model. Not all objects need to be selected, just the objects at the outer edge of where you want the collision.

---

## Joints
The `Joints` tab is used to create joints that can then be controlled in a simulation.

When creating a joint, a name and child link must be specified.
* After creation, you can use **`Adjust Joints`** to move and rotate joints without affecting the child link position and rotation.
* Use the **`Delete Joint`** button to remove unwanted joints.
* Use the **`Reset Joints`** button to return all joints to their rest position if you’ve manipulated them.

### Joint Hierarchy
The `Joint Hierarchy` section will show all your links and their parent/child hierarchy.

### Joint Properties
When a joint is selected, you can change its display size, set the parent link, and adjust its limits.

> **💡 Tips:**
> * Continuous joints are simply revolute joints with the **`Continuous Joint`** box checked in the joint properties.
> * Always use the **`Adjust Joint Positions/Rotations`** button to move joints.
> * Always use the **`Delete Joints`** button when removing a joint.
> * Ensure all joints have a parent link set.

---

## Materials
The `Materials` tab is used to set the visual material properties of objects, such as color and whether they appear metallic.

The `Material List` will show all materials that are applied to an object. Since materials can be applied to individual faces, one object can contain multiple materials.
* Use the **`+`** and **`-`** buttons to add and remove materials.
* Use the **`X`** button on the right to remove any materials that aren’t applied to any faces.

Set the material properties in the `Material Properties` panel. Use the **`Replace Material`** tool to replace the material with a preset material. Color information can be transferred using the **`Keep Color`** checkbox.

> **💡 Tips:**
> * `Metalness` should always be set to either `1` or `0`.
> * CAD models often have basic materials already applied. Use the `Replace Material` tool to quickly replace these with improved materials while retaining their association with objects/faces.
> * Use the standard material editor or the shader editor for more advanced material creation.
> * A material can be easily swapped for an existing material by clicking the sphere icon to the left of the material name.

---

## Export
The `Export` tab is where the SDF can be generated and all meshes will be exported.
1.  Choose your mesh format for visual meshes (e.g., `GLB` is recommended).
2.  Select a file path. The default **`//sdf_exports/`** will save the files to a folder called **`sdf_exports`** within the folder your blender file is saved. You must save the blender file first for this to work.
3.  After clicking **`Export SDF`**, a folder will be created containing the generated `model.sdf` file, along with all visual meshes in the chosen file format and any mesh colliders in the `STL` file format.

### Config file
Check the "export config" box and fill out the fields to export a model.config file.
