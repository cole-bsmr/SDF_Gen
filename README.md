# SDF_Gen Guide [WIP]

SDF_Gen is a Blender add-on for preparing 3D assets, building kinematics/joint hierarchies, generating collision geometry, and exporting simulation-ready SDF (Simulation Description Format) models.

---

## Installation

### 1. Install the Add-on in Blender

#### Method A: Symlink / Direct Folder (Recommended for Development)
Link or copy this repository folder into your Blender user scripts directory as `SDF_Gen`:

* **Linux:**
  ```bash
  ln -s /path/to/SDF_Gen ~/.config/blender/<version>/scripts/addons/SDF_Gen
  ```
* **macOS:**
  ```bash
  ln -s /path/to/SDF_Gen ~/Library/Application\ Support/Blender/<version>/scripts/addons/SDF_Gen
  ```
* **Windows (Command Prompt as Administrator):**
  ```cmd
  mklink /D "%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\SDF_Gen" "C:\path\to\SDF_Gen"
  ```

#### Method B: Install as Zip
1. Create a zip archive of the `SDF_Gen` folder.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. In the top-right menu (arrow icon), select **Install from Disk...** (or **Install...** in earlier Blender versions).
4. Select the `.zip` archive.
5. Search for **SDF Gen** and enable it by checking the checkbox.

The add-on panel will appear in the 3D Viewport sidebar (**N** key) under the **SDF_Gen** tab.

---

### 2. Optional Dependencies (Alpha Wrap Collider)

The **Alpha Wrap** collider generator requires [PyMeshLab](https://github.com/cnr-isti-vclab/PyMeshLab) to produce watertight, shrink-wrapped collision meshes. If you plan to use Alpha Wrap, install `pymeshlab` into **Blender's bundled Python environment**:

* **Linux:**
  ```bash
  /path/to/blender/<version>/python/bin/python3 -m pip install pymeshlab
  ```
* **macOS:**
  ```bash
  /Applications/Blender.app/Contents/Resources/<version>/python/bin/python3 -m pip install pymeshlab
  ```
* **Windows:**
  ```cmd
  "C:\Program Files\Blender Foundation\Blender <version>\<version>\python\bin\python.exe" -m pip install pymeshlab
  ```

*(Note: Standard primitive colliders and convex hull mesh colliders do not require external dependencies.)*

---

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

### Alpha Wrap Collider
Creates a watertight, shrink-wrapped 3D alpha-wrap collider around visual geometry. It runs asynchronously in the background so Blender remains responsive during computation.
* **`Alpha`**: Size of the probe ball / feature resolution (must be > 0). In percentage mode, this is a percentage of the bounding box diagonal (default: `2.0%`). In absolute mode, this is in meters (default: `0.02m`). Smaller values capture finer features but increase computation time significantly (halving Alpha roughly increases runtime by 3x to 8x as spatial cell counts scale between `1 / alpha^2` and `1 / alpha^3`).
* **`Offset`**: Surface offset / expansion distance added to the wrapped mesh (must be > 0). Default: `0.5%` (percentage mode) or `0.005m` (absolute mode).
* **`Mode`**: `Percentage` (relative to bounding box diagonal) or `Absolute` (meters). Switching between modes preserves the last entered values for each mode.
* **`Planar Angle`**: Dihedral angle limit in degrees using Blender's built-in Decimate Planar modifier to cleanly dissolve flat coplanar faces without generating overlapping or duplicate geometry (set to `0` to disable).
* **`Target Faces`**: Optional target face count simplification using Quadric Edge Collapse (set to `0` to disable).
* **`Per Object`**: Toggle whether to wrap each selected mesh individually or combine them into a single collider.
* **`Restore Defaults`**: Resets all Alpha Wrap parameters back to their recommended default values for the active mode.

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
