import bpy
import math
import numpy as np
import bmesh
from timeit import default_timer as timer
from mathutils import Matrix
import os
import sys
import tempfile
import threading
import mathutils
from ..operators.general_functions import show_message_box
from .alpha_wrap import alpha_wrap_mesh, is_pymeshlab_available






class MESH_OT_add_collider(bpy.types.Operator):
    bl_idname = "mesh.add_collider"
    bl_label = "Add Collider"
    bl_options = {"REGISTER", "UNDO"}

    shape_type: bpy.props.EnumProperty(
        name="Shape",
        description="The shape of collider.",
        items=[
            ("Box", "Box", "Create box collider"),
            ("Cylinder", "Cylinder", "Create cylinder collider"),
            ("Sphere", "Sphere", "Create sphere collider"),
            ("Cone", "Cone", "Create cone collider"),
            ("Plane", "Plane", "Create plane collider"),
            ("Mesh", "Mesh", "Create mesh collider"),
        ],
    )  # type: ignore

    axis_set: bpy.props.EnumProperty(
        name="Axis Set",
        description="The axis for the collider object to be aligned to.",
        items=[
            ("X", "X Axis", "Align to the X Axis"),
            ("Y", "Y Axis", "Align to the Y Axis"),
            ("Z", "Z Axis", "Align to the Z Axis"),
        ],
        default="Z",
    )  # type: ignore

    per_obj: bpy.props.BoolProperty(
        name="Per Object", description="Toggle for multiple selection behavior.", default=True
    )  # type: ignore

    plane_flip: bpy.props.BoolProperty(
        name="Flip direction", description="Flip the direction of plane collider normal.", default=False
    )  # type: ignore

    min_box: bpy.props.BoolProperty(
        name="Minimal Box",
        description="Box collider will be fit to the visual as tightly as possible.",
        default=False,
    )  # type: ignore

    mesh_resolution: bpy.props.FloatProperty(
        name="Mesh Resolution",
        description="Control the resolution of the mesh collider.",
        default=1.0,
        min=0,
        max=1,
        step=0.1,
    )  # type: ignore

    mesh_inflate: bpy.props.FloatProperty(
        name="Mesh Margin",
        description="Inflate the collision geometry to account for lower mesh resolution.",
        default=0,
        min=0,
        max=1,
        step=0.1,
    )  # type: ignore

    def invoke(self, context, event):
        self.plane_flip = False
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shape_type")

        if self.shape_type in {"Box"}:
            layout.prop(self, "min_box")
        if self.shape_type in {"Cylinder", "Cone", "Plane"}:
            layout.prop(self, "axis_set")
        if self.shape_type == "Plane":
            layout.prop(self, "plane_flip")

        layout.prop(self, "per_obj")

        if self.shape_type == "Mesh":
            layout.prop(self, "mesh_resolution")
            layout.prop(self, "mesh_inflate")

    def execute(self, context):
        if not validate_selection():
            return {"CANCELLED"}

        visual_mesh_objs = get_selected_mesh_objects()
        if not visual_mesh_objs:
            return {"CANCELLED"}

        bpy.context.view_layer.active_layer_collection = (
            bpy.context.view_layer.layer_collection
        )

        joined_visual = None
        ref_obj = visual_mesh_objs[0]

        # Join objects if per object is turned off
        if self.per_obj == False and len(visual_mesh_objs) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in visual_mesh_objs:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = visual_mesh_objs[0]
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.join()
            bpy.context.active_object.select_set(True)
            bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
            joined_visual = bpy.context.active_object
            target_objs = [joined_visual]
        else:
            target_objs = visual_mesh_objs

        created_colliders = []
        for visual_obj in target_objs:
            bpy.ops.object.select_all(action="DESELECT")
            visual_obj.select_set(True)
            bpy.context.view_layer.objects.active = visual_obj
            
            if self.shape_type == "Box" and self.min_box == False:
                box_collider(visual_obj)
            if self.shape_type == "Box" and self.min_box == True:
                obj_rotating_calipers_full(visual_obj)
            elif self.shape_type == "Cylinder":
                cylinder_collider(self.axis_set, visual_obj)
            elif self.shape_type == "Sphere":
                sphere_collider(visual_obj)
            elif self.shape_type == "Cone":
                cone_collider(self.axis_set, visual_obj)
            elif self.shape_type == "Plane":
                plane_collider(self.axis_set, visual_obj)
            elif self.shape_type == "Mesh":
                mesh_collider(visual_obj, self.mesh_resolution, self.mesh_inflate)

            collider_obj = bpy.context.active_object

            # Move collider to approprate collection
            move_to_collection(ref_obj if visual_obj == joined_visual else visual_obj, collider_obj)

            # Set the collider material and visibility settings
            SetColliderMaterial()

            # Rename collider
            collider_base_name = ref_obj.name if visual_obj == joined_visual else visual_obj.name
            collider_obj.name = (
                (collider_base_name + "_collider" + "_" + self.shape_type)
                .lower()
                .replace(".", "")
            )
            # Add the modifier that allows adjustment of the collider safety margin
            add_margin_modifier()
            created_colliders.append(collider_obj)
        
        # Remove duplicate object
        if joined_visual:
            bpy.data.objects.remove(joined_visual, do_unlink=True)

        # Select created colliders
        bpy.ops.object.select_all(action="DESELECT")
        for c in created_colliders:
            c.select_set(True)
        if created_colliders:
            bpy.context.view_layer.objects.active = created_colliders[0]

        return {"FINISHED"}


def move_to_collection(visual_obj, collider_obj):
    """Move the collider object to the appropriate '_colliders' collection."""
    visual_col = None
    curr = visual_obj
    while curr:
        for col in curr.users_collection:
            if "_visual" in col.name:
                visual_col = col
                break
        if visual_col:
            break
        curr = curr.parent

    if visual_col:
        collider_collection_name = visual_col.name.replace("_visual", "_colliders")
        if not bpy.data.collections.get(collider_collection_name):
            create_collection = bpy.data.collections.new(collider_collection_name)
            bpy.context.scene.collection.children.link(create_collection)
        target_col = bpy.data.collections[collider_collection_name]
        if collider_obj.name not in target_col.objects:
            target_col.objects.link(collider_obj)
        if collider_obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(collider_obj)



def SetColliderMaterial():
    """Assigns a transparent material to the given object."""
    # Set object's visibility settins for 'Solid' shading mode
    bpy.context.view_layer.objects.active.show_wire = True
    bpy.context.view_layer.objects.active.color = (1.0, 0.0, 1.0, 0.5)

    # Set shading mode to 'Object'
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    # Set viewport shading to 'OBJECT'
                    space.shading.color_type = "OBJECT"

    # Check if the material already exists
    material_name = "ColliderMaterial"
    material = bpy.data.materials.get(material_name)

    if not material:
        # Create the material if it doesn't exist
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()

        # Create nodes
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        emission_node = nodes.new(type="ShaderNodeEmission")
        mix_shader_node = nodes.new(type="ShaderNodeMixShader")
        output_node.location = (400, 0)
        principled_node.location = (0, 0)
        emission_node.location = (0, 200)
        mix_shader_node.location = (200, 0)

        # Set shader properties
        base_color = (1.0, 0.2, 0.6, 0.25)  # (R, G, B, A)
        principled_node.inputs["Base Color"].default_value = base_color
        principled_node.inputs["Alpha"].default_value = 0.25
        principled_node.inputs["Roughness"].default_value = 1.0
        emission_node.inputs["Color"].default_value = base_color[:3] + (
            1.0,
        )  # (R, G, B, 1.0)
        emission_node.inputs["Strength"].default_value = 1

        # Connect the nodes
        links.new(principled_node.outputs["BSDF"], mix_shader_node.inputs[1])
        links.new(emission_node.outputs["Emission"], mix_shader_node.inputs[2])
        links.new(mix_shader_node.outputs["Shader"], output_node.inputs["Surface"])

        # Set the render method and shadow options for transparency
        material.surface_render_method = (
            "BLENDED"  # Options: 'OPAQUE', 'BLENDED', 'DITHERED'
        )

    # Assign the material to the active object
    if bpy.context.active_object:
        obj = bpy.context.active_object
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)


def add_margin_modifier():
    """Add collider margin modifier"""
    cm_mod = bpy.context.active_object.modifiers.new(
        name="Collider Margin", type="SOLIDIFY"
    )
    cm_mod.offset = 1.0
    cm_mod.use_rim_only = True
    cm_mod.use_even_offset = True
    cm_mod.thickness = bpy.context.scene.collider_margin_thickness


def box_collider(visual_obj):
    """Create BOX collider"""

    bb_center = get_bb_center()
    bpy.ops.mesh.primitive_cube_add(
        location=bb_center,
        rotation=visual_obj.rotation_euler,
        scale=(
            visual_obj.dimensions.x / 2,
            visual_obj.dimensions.y / 2,
            visual_obj.dimensions.z / 2,
        ),
    )
    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "BoxCollider"


def cylinder_collider(axis_set, visual_obj):
    """Create CYLINDER collider"""

    bb_center = get_bb_center()
    bpy.ops.mesh.primitive_cylinder_add(
        location=bb_center,
        rotation=visual_obj.rotation_euler,
        scale=(
            visual_obj.dimensions.x / 2,
            visual_obj.dimensions.y / 2,
            visual_obj.dimensions.z / 2,
        ),
    )
    collider_obj = bpy.context.active_object

    ChangeOrientation(visual_obj, collider_obj, axis_set)

    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "CylinderCollider"


def sphere_collider(visual_obj):
    """Create SPHERE collider"""

    bb_center = get_bb_center()
    bpy.ops.mesh.primitive_uv_sphere_add(
        location=bb_center,
        rotation=visual_obj.rotation_euler,
        scale=(
            visual_obj.dimensions.x / 2,
            visual_obj.dimensions.y / 2,
            visual_obj.dimensions.z / 2,
        ),
    )

    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "SphereCollider"


def cone_collider(axis_set, visual_obj):
    """Create CONE collider"""

    bb_center = get_bb_center()
    bpy.ops.mesh.primitive_cone_add(
        location=bb_center,
        rotation=visual_obj.rotation_euler,
        scale=(
            visual_obj.dimensions.x / 2,
            visual_obj.dimensions.y / 2,
            visual_obj.dimensions.z / 2,
        ),
    )
    collider_obj = bpy.context.active_object

    ChangeOrientation(visual_obj, collider_obj, axis_set)

    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "ConeCollider"


def plane_collider(axis_set, visual_obj):
    """Create PLANE collider"""
    
    bb_center = get_bb_center()
    bpy.ops.mesh.primitive_plane_add(
        location=visual_obj.location,
        rotation=visual_obj.rotation_euler,
        scale=(
            visual_obj.dimensions.x / 2,
            visual_obj.dimensions.y / 2,
            visual_obj.dimensions.z / 2,
        ),
    )
    collider_obj = bpy.context.active_object

    if axis_set == "Z":
        collider_obj.dimensions = (visual_obj.dimensions.x, visual_obj.dimensions.y, 0)
        collider_obj.rotation_euler = visual_obj.rotation_euler
    if axis_set == "X":
        collider_obj.dimensions = (visual_obj.dimensions.x, visual_obj.dimensions.y, 0)
        collider_obj.rotation_euler = visual_obj.rotation_euler
        collider_obj.rotation_euler.rotate_axis("X", math.radians(90))
    if axis_set == "Y":
        collider_obj.dimensions = (visual_obj.dimensions.y, visual_obj.dimensions.z, 0)
        collider_obj.rotation_euler = visual_obj.rotation_euler
        collider_obj.rotation_euler.rotate_axis("Y", math.radians(90))

    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "PlaneCollider"


def mesh_collider(visual_obj, mesh_resolution, mesh_inflate):
    """Create MESH Collider"""

    # print (visual_obj)
    bpy.ops.object.select_all(action="DESELECT")
    visual_obj.select_set(True)
    bpy.ops.object.duplicate(linked=False)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode="OBJECT")

    if bpy.context.active_object.collider_type:
        print(bpy.context.active_object.collider_type)
    bpy.context.active_object.object_type = "ColliderObject"
    bpy.context.active_object.collider_type = "MeshCollider"
    if bpy.context.active_object.collider_type:
        print(bpy.context.active_object.collider_type)

    # Link the duplicate to the Scene Collection
    if bpy.context.active_object.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(bpy.context.active_object)

    # Remove the duplicate from any other collections
    for col in list(bpy.context.active_object.users_collection):
        if col != bpy.context.scene.collection:
            col.objects.unlink(bpy.context.active_object)

    # Add decimate modifier for mesh collider polygon count reduction
    cm_mod = bpy.context.active_object.modifiers.new(
        name="Mesh Collider Resolution", type="DECIMATE"
    )
    cm_mod.ratio = 1.0
    # Set mesh resolution property so it can be controlled via menu
    bpy.context.active_object.modifiers["Mesh Collider Resolution"].ratio = (
        mesh_resolution
    )

    # Add mesh collider margin for ensuring lower poly mesh collider fully encapsulates visual
    cm_mod = bpy.context.active_object.modifiers.new(
        name="Mesh Collider Margin", type="SOLIDIFY"
    )
    # Set values for modifier
    cm_mod.offset = 1.0
    cm_mod.use_rim_only = True
    cm_mod.use_even_offset = True
    cm_mod.thickness = 0.00
    # Set mesh margin property so it can be controlled via menu
    bpy.context.active_object.modifiers["Mesh Collider Margin"].thickness = mesh_inflate


def obj_rotating_calipers_full(obj, DEBUG=False):
    """Minimal box generation"""
    # Cube face indices for bounding box visualization
    CUBE_FACE_INDICES = (
        (0, 1, 3, 2),
        (2, 3, 7, 6),
        (6, 7, 5, 4),
        (4, 5, 1, 0),
        (2, 6, 4, 0),
        (7, 3, 1, 5),
    )

    def gen_cube_verts():
        for x in range(-1, 2, 2):
            for y in range(-1, 2, 2):
                for z in range(-1, 2, 2):
                    yield x, y, z

    def rotating_calipers(hull_points: np.ndarray, bases):
        min_bb_basis = None
        min_bb_min = None
        min_bb_max = None
        min_vol = math.inf
        for basis in bases:
            rot_points = hull_points.dot(np.linalg.inv(basis))
            bb_min = rot_points.min(axis=0)
            bb_max = rot_points.max(axis=0)
            volume = (bb_max - bb_min).prod()
            if volume < min_vol:
                min_bb_basis = basis
                min_vol = volume
                min_bb_min = bb_min
                min_bb_max = bb_max
        return np.array(min_bb_basis), min_bb_max, min_bb_min

    bm = bmesh.new()
    dg = bpy.context.evaluated_depsgraph_get()
    bm.from_object(obj, dg)

    # Calculate convex hull
    t0 = timer()
    chull_out = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    t1 = timer()
    print(f"Convex-Hull calculated in {t1-t0} sec")

    chull_geom = chull_out["geom"]
    chull_points = np.array(
        [bmelem.co for bmelem in chull_geom if isinstance(bmelem, bmesh.types.BMVert)]
    )

    # Create object from Convex-Hull (for debugging)
    if DEBUG:
        t0 = timer()
        for face in set(bm.faces) - set(chull_geom):
            bm.faces.remove(face)
        for edge in set(bm.edges) - set(chull_geom):
            bm.edges.remove(edge)
        t1 = timer()
        print(f"Deleted non Convex-Hull edges and faces in {t1 - t0} sec")

        chull_mesh = bpy.data.meshes.new(obj.name + "_convex_hull")
        chull_mesh.validate()
        bm.to_mesh(chull_mesh)
        chull_obj = bpy.data.objects.new(chull_mesh.name, chull_mesh)
        chull_obj.matrix_world = obj.matrix_world
        if chull_obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(chull_obj)

    # Create basis vectors for each face
    bases = []
    t0 = timer()
    for elem in chull_geom:
        if not isinstance(elem, bmesh.types.BMFace):
            continue
        if len(elem.verts) != 3:
            continue
        face_normal = elem.normal
        if np.allclose(face_normal, 0, atol=0.00001):
            continue
        for e in elem.edges:
            v0, v1 = e.verts
            edge_vec = (v0.co - v1.co).normalized()
            co_tangent = face_normal.cross(edge_vec)
            basis = (edge_vec, co_tangent, face_normal)
            bases.append(basis)

    t1 = timer()
    print(f"List of bases built in {t1-t0} sec")

    # Perform rotating calipers to get the minimum bounding box
    t0 = timer()
    bb_basis, bb_max, bb_min = rotating_calipers(chull_points, bases)
    t1 = timer()
    print(f"Rotating Calipers finished in {t1-t0} sec")

    bm.free()

    # Calculate final bounding box transformation
    bb_basis_mat = bb_basis.T
    bb_dim = bb_max - bb_min
    bb_center = (bb_max + bb_min) / 2
    mat = (
        Matrix.Translation(bb_center.dot(bb_basis))
        @ Matrix(bb_basis_mat).to_4x4()
        @ Matrix(np.identity(3) * bb_dim / 2).to_4x4()
    )

    # Create bounding box mesh and apply transformation
    bb_mesh = bpy.data.meshes.new(obj.name + "_minimum_bounding_box")
    bb_mesh.from_pydata(
        vertices=list(gen_cube_verts()), edges=[], faces=CUBE_FACE_INDICES
    )
    bb_mesh.validate()
    bb_mesh.update()
    bb_obj = bpy.data.objects.new(bb_mesh.name, bb_mesh)
    bb_obj.matrix_world = obj.matrix_world @ mat

    bb_obj.object_type = "ColliderObject"
    bb_obj.collider_type = "BoxCollider"

    if bb_obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(bb_obj)
    bpy.context.view_layer.objects.active = bb_obj


def ChangeOrientation(visual_obj, collider_obj, axis_set):
    """Sets collider orientation based on axis setting."""
    # Get the dimensions of the visual object
    x_dim, y_dim, z_dim = visual_obj.dimensions

    # Default orientation adjustments
    if axis_set == "Z":
        collider_obj.dimensions = (max(x_dim, y_dim), max(x_dim, y_dim), z_dim)
        collider_obj.rotation_euler = visual_obj.rotation_euler
    elif axis_set == "X":
        collider_obj.dimensions = (
            max(y_dim, z_dim),
            max(y_dim, z_dim),
            x_dim,
        )  # Set the height based on X
        collider_obj.rotation_euler = visual_obj.rotation_euler.copy()
        collider_obj.rotation_euler.rotate_axis(
            "Y", math.radians(90)
        )  # Rotate for correct axis alignment
    elif axis_set == "Y":
        collider_obj.dimensions = (
            max(x_dim, z_dim),
            max(x_dim, z_dim),
            y_dim,
        )  # Set the height based on Y
        collider_obj.rotation_euler = visual_obj.rotation_euler.copy()
        collider_obj.rotation_euler.rotate_axis(
            "X", math.radians(90)
        )  # Rotate for correct axis alignment


def get_selected_mesh_objects():
    """Traverses selected objects and their children recursively to collect all mesh objects."""
    if not bpy.context.selected_objects:
        return []

    meshes = []
    seen = set()

    def traverse(obj):
        if obj in seen:
            return
        seen.add(obj)
        # Filter out existing colliders
        is_collider = (
            getattr(obj, "object_type", "") == "ColliderObject"
            or getattr(obj, "collider_type", "NotCollider") != "NotCollider"
            or "_collider" in obj.name.lower()
        )
        if obj.type == "MESH" and not is_collider and obj not in meshes:
            meshes.append(obj)
        for child in obj.children:
            traverse(child)

    for obj in bpy.context.selected_objects:
        traverse(obj)

    return meshes


def validate_selection():
    """Validates that there is at least one mesh in the current selection or its children."""
    if not bpy.context.selected_objects:
        show_message_box(message="No object selected.", title="Error", icon="INFO")
        return False

    mesh_objs = get_selected_mesh_objects()
    if not mesh_objs:
        show_message_box(
            message="Selected object is not a mesh and has no mesh children.",
            title="Error",
            icon="INFO",
        )
        return False

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    return True


def get_bb_center():
    obj = bpy.context.active_object  # Replace with your object if not using the active one

    # Get the bounding box center in local space
    bb_min = mathutils.Vector(obj.bound_box[0])
    bb_max = mathutils.Vector(obj.bound_box[6])
    bb_center_local = (bb_min + bb_max) / 2

    # Convert to world space
    bb_center_world = obj.matrix_world @ bb_center_local

    return bb_center_world


def export_object_to_stl(obj, filepath):
    """Exports a single object to an STL file on the main thread."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if hasattr(bpy.ops.wm, "stl_export"):
        bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=True,
            apply_modifiers=True,
        )
    elif hasattr(bpy.ops.export_mesh, "stl"):
        bpy.ops.export_mesh.stl(
            filepath=filepath,
            use_selection=True,
            use_mesh_modifiers=True,
        )
    else:
        raise RuntimeError("No STL export operator available in Blender.")


def import_stl_object(filepath):
    """Imports an STL file as a new Blender object and returns it."""
    bpy.ops.object.select_all(action="DESELECT")
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=filepath)
    elif hasattr(bpy.ops.import_mesh, "stl"):
        bpy.ops.import_mesh.stl(filepath=filepath)
    else:
        raise RuntimeError("No STL import operator available in Blender.")

    imported_obj = bpy.context.active_object
    if not imported_obj:
        raise RuntimeError("Failed to import STL mesh into Blender.")
    return imported_obj


def setup_alpha_wrap_collider(collider_obj, visual_obj, target_name):
    """Configures and positions an imported STL object as an Alpha Wrap collider."""
    bpy.context.view_layer.objects.active = collider_obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

    collider_obj.object_type = "ColliderObject"
    collider_obj.collider_type = "MeshCollider"

    # Ensure object is linked to scene collection before moving
    if collider_obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(collider_obj)
    for col in list(collider_obj.users_collection):
        if col != bpy.context.scene.collection:
            col.objects.unlink(collider_obj)

    # Move to the appropriate _colliders collection
    if visual_obj:
        move_to_collection(visual_obj, collider_obj)

    # Set collider material and wireframe display
    SetColliderMaterial()

    # Set final collider name
    collider_obj.name = target_name

    # Add the margin modifier
    add_margin_modifier()


def tag_redraw_view3d():
    """Redraws 3D Viewport areas to refresh the SDF_Gen sidebar panel."""
    wm = bpy.context.window_manager
    if not wm:
        return
    for window in wm.windows:
        if window.screen:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()


def _cleanup_task_files(tasks):
    """Deletes temporary STL files associated with alpha wrap tasks."""
    for task in tasks:
        for path in (task.get("temp_in"), task.get("temp_out")):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _alpha_wrap_worker(tasks, params, state):
    """Background worker function executing heavy alpha-wrap processing."""
    try:
        total = len(tasks)
        for i, task in enumerate(tasks):
            state["current"] = i
            state["status"] = (
                f"Wrapping ({i + 1}/{total})..." if total > 1 else "Wrapping..."
            )
            alpha_wrap_mesh(
                input_path=task["temp_in"],
                output_path=task["temp_out"],
                alpha=params["alpha"],
                offset=params["offset"],
                is_percentage=params["is_percentage"],
                decimate_angle=params["decimate_angle"],
                decimate_faces=params["decimate_faces"],
            )
            state["completed"] = i + 1
    except Exception as e:
        state["error"] = str(e)
    finally:
        state["is_done"] = True


def _create_wrap_timer_callback(tasks, state):
    """Creates a timer callback function to monitor and finalize alpha wrap on the main thread."""
    last_status = [None]

    def timer_callback():
        wm = bpy.context.window_manager

        # While worker thread is still computing in background
        if not state.get("is_done", False):
            current_status = state.get("status", "Wrapping...")
            if wm and current_status != last_status[0]:
                wm.alpha_wrap_status = current_status
                last_status[0] = current_status
                tag_redraw_view3d()
            return 0.1

        # Background computation finished - running on Main Thread
        if wm:
            wm.alpha_wrap_in_progress = False
            wm.alpha_wrap_status = ""

        err = state.get("error")
        if err:
            _cleanup_task_files(tasks)
            show_message_box(
                message=f"Alpha Wrap failed: {err}",
                title="Error",
                icon="ERROR",
            )
            tag_redraw_view3d()
            return None

        created_colliders = []
        try:
            for task in tasks:
                temp_out = task["temp_out"]
                visual_obj = bpy.data.objects.get(task["visual_obj_name"])

                if not os.path.exists(temp_out) or os.path.getsize(temp_out) == 0:
                    continue

                collider_obj = import_stl_object(temp_out)
                setup_alpha_wrap_collider(
                    collider_obj=collider_obj,
                    visual_obj=visual_obj,
                    target_name=task["target_name"],
                )
                created_colliders.append(collider_obj)

            # Select newly created colliders
            bpy.ops.object.select_all(action="DESELECT")
            for c in created_colliders:
                c.select_set(True)
            if created_colliders:
                bpy.context.view_layer.objects.active = created_colliders[0]

            if hasattr(bpy.ops.ed, "undo_push"):
                try:
                    bpy.ops.ed.undo_push(message="Create Alpha Wrap Collider")
                except Exception:
                    pass

        except Exception as e:
            show_message_box(
                message=f"Failed finalizing Alpha Wrap colliders: {str(e)}",
                title="Error",
                icon="ERROR",
            )
        finally:
            _cleanup_task_files(tasks)

        tag_redraw_view3d()
        return None

    return timer_callback


def alpha_wrap_collider(
    visual_obj,
    alpha,
    offset,
    is_percentage,
    decimate_angle,
    decimate_faces,
):
    """Synchronously creates a new alpha-wrapped collision mesh object from visual_obj."""
    temp_in = tempfile.mktemp(suffix=".stl")
    temp_out = tempfile.mktemp(suffix=".stl")

    try:
        export_object_to_stl(visual_obj, temp_in)
        alpha_wrap_mesh(
            input_path=temp_in,
            output_path=temp_out,
            alpha=alpha,
            offset=offset,
            is_percentage=is_percentage,
            decimate_angle=decimate_angle,
            decimate_faces=decimate_faces,
        )
        if not os.path.exists(temp_out) or os.path.getsize(temp_out) == 0:
            raise RuntimeError("Alpha wrap produced an empty or missing output mesh.")

        collider_obj = import_stl_object(temp_out)
        target_name = (
            (visual_obj.name + "_collider_alphawrap")
            .lower()
            .replace(".", "")
        )
        setup_alpha_wrap_collider(collider_obj, visual_obj, target_name)
        return collider_obj

    finally:
        for p in (temp_in, temp_out):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


class MESH_OT_create_alpha_wrap_collider(bpy.types.Operator):
    bl_idname = "mesh.create_alpha_wrap_collider"
    bl_label = "Create Alpha Wrap Collider"
    bl_description = "Generates a watertight, shrink-wrapped Alpha Wrap collision mesh from selected visual objects or their hierarchy asynchronously"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not is_pymeshlab_available():
            msg = (
                "PyMeshLab is not installed in Blender's Python environment.\n"
                "To enable Alpha Wrap, install PyMeshLab in Blender via:\n"
                f"{sys.executable} -m pip install pymeshlab"
            )
            show_message_box(message=msg, title="PyMeshLab Missing", icon="ERROR")
            self.report(
                {"WARNING"},
                "PyMeshLab is not installed in Blender's Python environment.",
            )
            return {"CANCELLED"}

        if context.window_manager.alpha_wrap_in_progress:
            self.report(
                {"WARNING"},
                "Alpha wrap is already in progress.",
            )
            return {"CANCELLED"}

        scene = context.scene
        alpha = scene.alpha_wrap_alpha
        offset = scene.alpha_wrap_offset

        if alpha <= 0.0 or offset <= 0.0:
            errors = []
            if alpha <= 0.0:
                errors.append(
                    f"Alpha must be strictly positive (> 0), but is set to {alpha:.4g}."
                )
            if offset <= 0.0:
                errors.append(
                    f"Offset must be strictly positive (> 0), but is set to {offset:.4g}."
                )
            error_message = "\n".join(errors)
            show_message_box(
                message=error_message,
                title="Invalid Alpha Wrap Parameters",
                icon="ERROR",
            )
            self.report({"ERROR"}, error_message.replace("\n", " "))
            return {"CANCELLED"}

        if not validate_selection():
            return {"CANCELLED"}

        bpy.context.view_layer.active_layer_collection = (
            bpy.context.view_layer.layer_collection
        )

        is_percentage = (scene.alpha_wrap_mode == "PERCENTAGE")
        decimate_angle = (
            scene.alpha_wrap_decimate_angle
            if scene.alpha_wrap_decimate_angle > 0
            else None
        )
        decimate_faces = (
            scene.alpha_wrap_decimate_faces
            if scene.alpha_wrap_decimate_faces > 0
            else None
        )
        per_obj = scene.alpha_wrap_per_obj

        selected_objs = get_selected_mesh_objects()
        if not selected_objs:
            show_message_box(
                message="Selected object is not a mesh and has no mesh children.",
                title="Error",
                icon="INFO",
            )
            return {"CANCELLED"}

        tasks = []
        try:
            if not per_obj and len(selected_objs) > 1:
                # Combine duplicates for wrapping into a single collider
                bpy.ops.object.select_all(action="DESELECT")
                for obj in selected_objs:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = selected_objs[0]
                bpy.ops.object.duplicate(linked=False)
                bpy.ops.object.join()
                temp_joined = bpy.context.active_object
                temp_in = tempfile.mktemp(suffix=".stl")
                temp_out = tempfile.mktemp(suffix=".stl")
                try:
                    export_object_to_stl(temp_joined, temp_in)
                finally:
                    bpy.data.objects.remove(temp_joined, do_unlink=True)

                target_name = (
                    (selected_objs[0].name + "_collider_alphawrap")
                    .lower()
                    .replace(".", "")
                )
                tasks.append({
                    "temp_in": temp_in,
                    "temp_out": temp_out,
                    "visual_obj_name": selected_objs[0].name,
                    "target_name": target_name,
                })
            else:
                for visual_obj in selected_objs:
                    temp_in = tempfile.mktemp(suffix=".stl")
                    temp_out = tempfile.mktemp(suffix=".stl")
                    export_object_to_stl(visual_obj, temp_in)
                    target_name = (
                        (visual_obj.name + "_collider_alphawrap")
                        .lower()
                        .replace(".", "")
                    )
                    tasks.append({
                        "temp_in": temp_in,
                        "temp_out": temp_out,
                        "visual_obj_name": visual_obj.name,
                        "target_name": target_name,
                    })

            # Restore original selection
            bpy.ops.object.select_all(action="DESELECT")
            for obj in selected_objs:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = selected_objs[0]

        except Exception as e:
            _cleanup_task_files(tasks)
            show_message_box(
                message=f"Failed preparing Alpha Wrap tasks: {str(e)}",
                title="Error",
                icon="ERROR",
            )
            return {"CANCELLED"}

        wm = context.window_manager
        wm.alpha_wrap_in_progress = True
        initial_status = (
            f"Wrapping (0/{len(tasks)})..." if len(tasks) > 1 else "Wrapping..."
        )
        wm.alpha_wrap_status = initial_status

        params = {
            "alpha": alpha,
            "offset": offset,
            "is_percentage": is_percentage,
            "decimate_angle": decimate_angle,
            "decimate_faces": decimate_faces,
        }
        state = {
            "completed": 0,
            "total": len(tasks),
            "status": initial_status,
            "error": None,
            "is_done": False,
        }

        # Start background worker thread
        thread = threading.Thread(
            target=_alpha_wrap_worker,
            args=(tasks, params, state),
            daemon=True,
        )
        thread.start()

        # Register non-blocking timer on main thread
        timer_cb = _create_wrap_timer_callback(tasks, state)
        bpy.app.timers.register(timer_cb, first_interval=0.05)

        tag_redraw_view3d()
        self.report(
            {"INFO"},
            f"Alpha wrap started for {len(tasks)} mesh object(s) in background...",
        )
        return {"FINISHED"}


class MESH_OT_restore_alpha_wrap_defaults(bpy.types.Operator):
    bl_idname = "mesh.restore_alpha_wrap_defaults"
    bl_label = "Restore Defaults"
    bl_description = "Restores Alpha Wrap parameters to default values for the active mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene

        # Reset stored mode defaults
        scene.alpha_wrap_alpha_percentage = 2.0
        scene.alpha_wrap_offset_percentage = 0.5
        scene.alpha_wrap_alpha_absolute = 0.02
        scene.alpha_wrap_offset_absolute = 0.005

        # Update active properties based on current mode
        if scene.alpha_wrap_mode == "PERCENTAGE":
            scene.alpha_wrap_alpha = 2.0
            scene.alpha_wrap_offset = 0.5
        else:
            scene.alpha_wrap_alpha = 0.02
            scene.alpha_wrap_offset = 0.005

        scene.alpha_wrap_decimate_angle = 5.0
        scene.alpha_wrap_decimate_faces = 0
        scene.alpha_wrap_per_obj = True

        self.report({"INFO"}, "Alpha Wrap default parameters restored.")
        return {"FINISHED"}


