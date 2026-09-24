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
import subprocess
import mathutils
import hashlib
import shutil
from ..operators.general_functions import show_message_box
from .alpha_wrap import alpha_wrap_mesh, is_pymeshlab_available, get_blender_python_executable
from .properties import (
    DEFAULT_ALPHA_ABSOLUTE,
    DEFAULT_ALPHA_PERCENTAGE,
    DEFAULT_OFFSET_ABSOLUTE,
    DEFAULT_OFFSET_PERCENTAGE,
)


def _get_selected_colliders_poly_count(context) -> int:
    """Computes total evaluated polygon count for selected collider objects or active collider."""
    try:
        dg = context.evaluated_depsgraph_get()
        colliders = [
            obj for obj in context.selected_objects
            if getattr(obj, "object_type", "") == "ColliderObject" and obj.type == "MESH"
        ]
        if not colliders and context.active_object:
            if getattr(context.active_object, "object_type", "") == "ColliderObject" and context.active_object.type == "MESH":
                colliders = [context.active_object]

        total = 0
        for col_obj in colliders:
            eval_obj = col_obj.evaluated_get(dg)
            total += len(eval_obj.data.polygons)
        return total
    except Exception:
        return 0



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

    decimate_mod_ratio: bpy.props.FloatProperty(
        name="Decimation Ratio",
        description="Decimation ratio for the mesh collider. Lower values reduce polygon count.\n"
        "The value range is [1.0,  0.0) and represents the fraction of polygons to retain.\n"
        "1.0 means no decimation; 0.1 is an aggressive decimation and only retains 10% of polygons.\n"
        "The decimation algorithm is the the edge-collapse modifier of Blender's built-in Decimate modifier.\n"
        "It ranks the edges of the mesh by a cost function and collapses the edges with the least "
        "impact on the shape of the mesh first.",
        default=1.0,
        min=0,
        max=1,
        step=0.1,
    )  # type: ignore

    mesh_inflate: bpy.props.FloatProperty(
        name="Mesh Margin",
        description="Inflate the collision geometry to account for lower mesh resolution (in mm).",
        default=0.0,
        min=0.0,
        soft_max=10.0,
        step=10,
    )  # type: ignore

    def invoke(self, context, event):
        self.plane_flip = False
        self.decimate_mod_ratio = 1.0
        self.mesh_inflate = 0.0
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
            layout.prop(self, "decimate_mod_ratio")
            layout.prop(self, "mesh_inflate")
            poly_count = _get_selected_colliders_poly_count(context)
            layout.label(text=f"Polygons: {poly_count:,}")

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
                mesh_collider(visual_obj, self.decimate_mod_ratio, self.mesh_inflate)

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


def mesh_collider(visual_obj, decimate_mod_ratio, mesh_inflate):
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
        name="Decimation Ratio", type="DECIMATE"
    )
    cm_mod.ratio = 1.0
    # Set decimate property so it can be controlled via menu
    bpy.context.active_object.modifiers["Decimation Ratio"].ratio = (
        decimate_mod_ratio
    )

    # Add mesh collider margin for ensuring lower poly mesh collider fully encapsulates visual
    cm_mod = bpy.context.active_object.modifiers.new(
        name="Mesh Collider Margin", type="SOLIDIFY"
    )
    # Set values for modifier
    cm_mod.offset = 1.0
    cm_mod.use_rim_only = True
    cm_mod.use_even_offset = True
    # Set mesh margin property so it can be controlled via menu (1 = 1mm)
    bpy.context.active_object.modifiers["Mesh Collider Margin"].thickness = (
        mesh_inflate * 0.001
    )


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


def get_alpha_wrap_targets():
    """Returns mesh objects to process for alpha wrap.
    If visual meshes are selected (or children of selection), returns them.
    If only colliders are selected, resolves them back to their source visual mesh objects."""
    selected_objs = get_selected_mesh_objects()
    if selected_objs:
        return selected_objs

    resolved = []
    seen = set()
    for obj in bpy.context.selected_objects:
        # Check stored source_visuals list property (for joined colliders)
        source_names = obj.get("source_visuals")
        if source_names:
            found_any = False
            for sname in source_names:
                if sname in bpy.data.objects:
                    src = bpy.data.objects[sname]
                    if src.type == "MESH" and src not in seen:
                        seen.add(src)
                        resolved.append(src)
                        found_any = True
            if found_any:
                continue

        # Check stored source_visual custom property
        source_name = obj.get("source_visual")
        if source_name and source_name in bpy.data.objects:
            src = bpy.data.objects[source_name]
            if src.type == "MESH" and src not in seen:
                seen.add(src)
                resolved.append(src)
                continue

        # Check by name prefix (e.g. jaw_collider_alphawrap -> jaw)
        obj_name_lower = obj.name.lower()
        if "_collider" in obj_name_lower:
            base_name = obj_name_lower.split("_collider")[0]
            for candidate in bpy.data.objects:
                if candidate.type != "MESH":
                    continue
                cand_is_collider = (
                    getattr(candidate, "object_type", "") == "ColliderObject"
                    or getattr(candidate, "collider_type", "NotCollider") != "NotCollider"
                    or "_collider" in candidate.name.lower()
                )
                if not cand_is_collider and candidate.name.lower().replace(".", "") == base_name:
                    if candidate not in seen:
                        seen.add(candidate)
                        resolved.append(candidate)
                    break

    return resolved


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


def apply_planar_decimate_modifier(collider_obj, angle_deg: float):
    """Simplifies coplanar faces using Blender's built-in Decimate -> Planar modifier."""
    if angle_deg is None or angle_deg <= 0.0 or not collider_obj.data.polygons:
        return
    mod = collider_obj.modifiers.new(name="Alpha Wrap Planar Decimate", type="DECIMATE")
    mod.decimate_type = "DISSOLVE"
    mod.angle_limit = math.radians(angle_deg)
    prev_active = bpy.context.view_layer.objects.active
    try:
        bpy.context.view_layer.objects.active = collider_obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as e:
        print(f"Warning: Failed to apply Decimate Planar modifier: {e}")
    finally:
        bpy.context.view_layer.objects.active = prev_active


def setup_alpha_wrap_collider(
    collider_obj,
    visual_obj,
    target_name,
    decimate_mod_ratio=1.0,
    source_visual_names=None,
):
    """Configures and positions an imported STL object as an Alpha Wrap collider."""
    bpy.context.view_layer.objects.active = collider_obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

    # Add decimate modifier for mesh collider polygon count reduction
    cm_mod = collider_obj.modifiers.new(
        name="Decimation Ratio", type="DECIMATE"
    )
    cm_mod.ratio = decimate_mod_ratio

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

    # Remove any existing collider with target_name to prevent duplicate .001 meshes
    existing_obj = bpy.data.objects.get(target_name)
    if existing_obj and existing_obj != collider_obj:
        mesh_data = existing_obj.data
        bpy.data.objects.remove(existing_obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

    # Set collider material and wireframe display
    SetColliderMaterial()

    # Set final collider name
    collider_obj.name = target_name
    if visual_obj:
        collider_obj["source_visual"] = visual_obj.name
    if source_visual_names:
        collider_obj["source_visuals"] = list(source_visual_names)

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



def alpha_wrap_collider(
    visual_obj,
    alpha,
    offset,
    is_percentage,
    decimate_mod_ratio=1.0,
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
        )
        if not os.path.exists(temp_out) or os.path.getsize(temp_out) == 0:
            raise RuntimeError("Alpha wrap produced an empty or missing output mesh.")

        collider_obj = import_stl_object(temp_out)
        target_name = (
            (visual_obj.name + "_collider_alphawrap")
            .lower()
            .replace(".", "")
        )
        setup_alpha_wrap_collider(
            collider_obj=collider_obj,
            visual_obj=visual_obj,
            target_name=target_name,
            decimate_mod_ratio=decimate_mod_ratio,
        )
        return collider_obj

    finally:
        for p in (temp_in, temp_out):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


MIN_ALPHA_PERCENTAGE = 0.5
MIN_OFFSET_PERCENTAGE = 0.01
# Percentages refer to the bounding box diagonal, so values above 100% are meaningless.
MAX_PERCENTAGE = 100.0


def _get_object_world_bbox_diagonal(obj) -> float:
    """Computes the world-space axis-aligned bounding box diagonal of a mesh object."""
    try:
        if obj.type == "MESH" and obj.data and len(obj.data.vertices) > 0:
            n_verts = len(obj.data.vertices)
            coords = np.empty(n_verts * 3, dtype=np.float64)
            obj.data.vertices.foreach_get("co", coords)
            coords = coords.reshape(-1, 3)
            mat = np.array(obj.matrix_world, dtype=np.float64)
            world_coords = coords @ mat[:3, :3].T + mat[:3, 3]
            extents = world_coords.max(axis=0) - world_coords.min(axis=0)
            return float(np.linalg.norm(extents))
        corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
        pts = np.array([[c.x, c.y, c.z] for c in corners], dtype=np.float64)
        extents = pts.max(axis=0) - pts.min(axis=0)
        return float(np.linalg.norm(extents))
    except Exception:
        return 1.0


def _get_combined_world_bbox_diagonal(objs) -> float:
    """Computes the combined world-space axis-aligned bounding box diagonal of multiple objects."""
    if not objs:
        return 1.0
    all_mins = []
    all_maxs = []
    for obj in objs:
        try:
            if obj.type == "MESH" and obj.data and len(obj.data.vertices) > 0:
                n_verts = len(obj.data.vertices)
                coords = np.empty(n_verts * 3, dtype=np.float64)
                obj.data.vertices.foreach_get("co", coords)
                coords = coords.reshape(-1, 3)
                mat = np.array(obj.matrix_world, dtype=np.float64)
                world_coords = coords @ mat[:3, :3].T + mat[:3, 3]
                all_mins.append(world_coords.min(axis=0))
                all_maxs.append(world_coords.max(axis=0))
            else:
                corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
                pts = np.array([[c.x, c.y, c.z] for c in corners], dtype=np.float64)
                all_mins.append(pts.min(axis=0))
                all_maxs.append(pts.max(axis=0))
        except Exception:
            pass
    if not all_mins:
        return 1.0
    global_min = np.min(all_mins, axis=0)
    global_max = np.max(all_maxs, axis=0)
    return float(np.linalg.norm(global_max - global_min))


def get_alpha_wrap_bbox_diagonal(per_obj: bool, target_objs=None) -> float:
    """Returns the world-space bounding box diagonal the Alpha Wrap values relate to.

    With per_obj disabled all targets are wrapped as one mesh, so their combined
    bounding box applies. Otherwise every target is wrapped on its own and the largest
    one is decisive, because it is the object for which a given Alpha resolves into the
    highest number of spatial cells.
    """
    if target_objs is None:
        target_objs = get_alpha_wrap_targets()

    # Object world matrices are evaluated by the dependency graph. Every Redo panel
    # re-run is preceded by an undo step, after which the matrices can still be stale
    # and lack transforms inherited from parents. Measuring them in that state yields a
    # bounding box in the unit scale of the raw mesh data (e.g. millimetres for CAD
    # imports parented under a scaled empty), so the graph must be flushed first.
    bpy.context.view_layer.update()

    if not target_objs:
        return 1.0
    if not per_obj and len(target_objs) > 1:
        diag = _get_combined_world_bbox_diagonal(target_objs)
    else:
        diags = [_get_object_world_bbox_diagonal(o) for o in target_objs]
        diag = max(diags) if diags else 1.0

    return diag if diag > 0.0 else 1.0


def get_alpha_wrap_min_values(mode: str, per_obj: bool, target_objs=None):
    """Returns (min_alpha, min_offset) for the given mode and target objects."""
    if mode == "PERCENTAGE":
        return MIN_ALPHA_PERCENTAGE, MIN_OFFSET_PERCENTAGE

    diag = get_alpha_wrap_bbox_diagonal(per_obj, target_objs)
    min_alpha = diag * (MIN_ALPHA_PERCENTAGE / 100.0)
    min_offset = diag * (MIN_OFFSET_PERCENTAGE / 100.0)
    return min_alpha, min_offset


def get_seeded_absolute_values(per_obj: bool, target_objs=None):
    """Returns the (alpha, offset) an absolute mode session should start with.

    An absolute length is only meaningful for the object it was measured on, so the
    values are derived from the current targets, using the same ratios as the
    percentage mode defaults.
    """
    diag = get_alpha_wrap_bbox_diagonal(per_obj, target_objs)
    return (
        diag * (DEFAULT_ALPHA_PERCENTAGE / 100.0),
        diag * (DEFAULT_OFFSET_PERCENTAGE / 100.0),
    )


_last_alpha_wrap_mode = None
_last_alpha_wrap_per_obj = None


class MESH_OT_create_alpha_wrap_collider(bpy.types.Operator):
    bl_idname = "mesh.create_alpha_wrap_collider"
    bl_label = "Create Alpha Wrap Collider"
    bl_description = "Generates a watertight, shrink-wrapped Alpha Wrap collision mesh from selected visual objects or their hierarchy"
    bl_options = {"REGISTER", "UNDO"}

    # Mode active during the previous execution. Used to detect a mode switch so the
    # values remembered for the newly selected mode can be restored. Must persist
    # across Redo panel re-runs, so it must not use SKIP_SAVE.
    prev_mode: bpy.props.StringProperty(
        default="",
        options={"HIDDEN"},
    )

    # Last Alpha and Offset entered for each mode, restored when the user switches
    # back to that mode. This memory lives on the operator and not on the scene,
    # because every Redo panel re-run is preceded by an undo, which restores the scene
    # and would roll scene-held values back to their state before the first run.
    alpha_memory_percentage: bpy.props.FloatProperty(
        default=DEFAULT_ALPHA_PERCENTAGE,
        options={"HIDDEN"},
    )

    offset_memory_percentage: bpy.props.FloatProperty(
        default=DEFAULT_OFFSET_PERCENTAGE,
        options={"HIDDEN"},
    )

    alpha_memory_absolute: bpy.props.FloatProperty(
        default=DEFAULT_ALPHA_ABSOLUTE,
        options={"HIDDEN"},
    )

    offset_memory_absolute: bpy.props.FloatProperty(
        default=DEFAULT_OFFSET_ABSOLUTE,
        options={"HIDDEN"},
    )

    alpha: bpy.props.FloatProperty(
        name="Alpha",
        description=(
            "Probe ball radius / feature resolution: controls how tightly the wrap conforms to the surface.\n"
            "Smaller values capture finer geometric details; larger values bridge holes and gaps.\n"
            "Clamped to a minimum of 0.5% of the bounding box diagonal"
        ),
        default=2.0,
        min=1e-6,
        soft_min=1e-6,
        precision=4,
    )

    offset: bpy.props.FloatProperty(
        name="Offset",
        description=(
            "Offset distance: thickness added outward from the input surface.\n"
            "Guarantees the collision wrap strictly encloses the visual mesh.\n"
            "Clamped to a minimum of 0.01% of the bounding box diagonal"
        ),
        default=0.5,
        min=1e-6,
        soft_min=1e-6,
        precision=4,
    )

    mode: bpy.props.EnumProperty(
        name="Mode",
        description="Coordinate units used for Alpha and Offset values",
        items=[
            (
                "PERCENTAGE",
                "Percentage",
                "Values are calculated as a percentage of the bounding box diagonal",
            ),
            (
                "ABSOLUTE",
                "Absolute",
                "Values are in absolute metric units (meters)",
            ),
        ],
        default="PERCENTAGE",
    )

    decimate_mod_ratio: bpy.props.FloatProperty(
        name="Decimation Ratio",
        description="Decimation ratio for the mesh collider. Lower values reduce polygon count.\n"
        "The value range is [1.0,  0.0) and represents the fraction of polygons to retain.\n"
        "1.0 means no decimation; 0.1 is an aggressive decimation and only retains 10% of polygons.\n"
        "The decimation algorithm is the the edge-collapse modifier of Blender's built-in Decimate modifier.\n"
        "It ranks the edges of the mesh by a cost function and collapses the edges with the least "
        "impact on the shape of the mesh first.",
        default=1.0,
        min=0.0,
        max=1.0,
        step=0.1,
    )

    per_obj: bpy.props.BoolProperty(
        name="Per Object",
        description="Toggle for multiple selection behavior.",
        default=False,
    )

    def invoke(self, context, event):
        global _last_alpha_wrap_mode, _last_alpha_wrap_per_obj
        if not is_pymeshlab_available():
            return bpy.ops.mesh.install_pymeshlab("INVOKE_DEFAULT")

        # Always return all values to their clean defaults when invoked for a new object or selection
        self.mode = "PERCENTAGE"
        self.prev_mode = "PERCENTAGE"
        _last_alpha_wrap_mode = "PERCENTAGE"
        self.per_obj = False
        _last_alpha_wrap_per_obj = False

        self.alpha_memory_percentage = DEFAULT_ALPHA_PERCENTAGE
        self.offset_memory_percentage = DEFAULT_OFFSET_PERCENTAGE
        self.alpha_memory_absolute, self.offset_memory_absolute = (
            get_seeded_absolute_values(self.per_obj)
        )

        self.alpha = DEFAULT_ALPHA_PERCENTAGE
        self.offset = DEFAULT_OFFSET_PERCENTAGE
        self.decimate_mod_ratio = 1.0

        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.prop(self, "alpha")
        col.prop(self, "offset")
        col.prop(self, "mode")
        col.prop(self, "decimate_mod_ratio")
        poly_count = _get_selected_colliders_poly_count(context)
        col.label(text=f"Polygons: {poly_count:,}")
        col.prop(self, "per_obj")

    def execute(self, context):
        global _last_alpha_wrap_mode, _last_alpha_wrap_per_obj
        if not is_pymeshlab_available():
            bpy.ops.mesh.install_pymeshlab("INVOKE_DEFAULT")
            return {"CANCELLED"}

        if not bpy.context.selected_objects:
            show_message_box(message="No object selected.", title="Error", icon="INFO")
            return {"CANCELLED"}

        selected_objs = get_alpha_wrap_targets()
        if not selected_objs:
            show_message_box(
                message="Selected object is not a mesh and has no mesh children.",
                title="Error",
                icon="INFO",
            )
            return {"CANCELLED"}

        scene = context.scene

        # Default to Absolute mode when switching to Per Object mode to prevent
        # extreme processing times caused by tiny relative percentage values on small parts.
        if _last_alpha_wrap_per_obj is False and self.per_obj:
            if self.mode != "ABSOLUTE":
                self.mode = "ABSOLUTE"
                seeded_alpha, seeded_offset = get_seeded_absolute_values(True, selected_objs)
                self.alpha_memory_absolute = seeded_alpha
                self.offset_memory_absolute = seeded_offset
        _last_alpha_wrap_per_obj = self.per_obj

        # A mode switch keeps the values previously entered for the newly selected mode
        # instead of converting the current value, which would otherwise drift on every
        # Redo panel re-run.
        last_mode = _last_alpha_wrap_mode if _last_alpha_wrap_mode is not None else self.prev_mode
        if last_mode and last_mode != self.mode:
            if self.mode == "PERCENTAGE":
                self.alpha = self.alpha_memory_percentage
                self.offset = self.offset_memory_percentage
            else:
                self.alpha = self.alpha_memory_absolute
                self.offset = self.offset_memory_absolute
        self.prev_mode = self.mode
        _last_alpha_wrap_mode = self.mode

        min_alpha, min_offset = get_alpha_wrap_min_values(
            self.mode, self.per_obj, selected_objs
        )
        if self.alpha < min_alpha:
            self.alpha = min_alpha
        if self.offset < min_offset:
            self.offset = min_offset

        # In percentage mode the values cannot exceed the full bounding box diagonal.
        if self.mode == "PERCENTAGE":
            self.alpha = min(self.alpha, MAX_PERCENTAGE)
            self.offset = min(self.offset, MAX_PERCENTAGE)

        # Remember the values of the active mode, so switching away and back restores
        # them instead of the defaults.
        if self.mode == "PERCENTAGE":
            self.alpha_memory_percentage = self.alpha
            self.offset_memory_percentage = self.offset
        else:
            self.alpha_memory_absolute = self.alpha
            self.offset_memory_absolute = self.offset

        alpha = self.alpha
        offset = self.offset

        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.context.view_layer.active_layer_collection = (
            bpy.context.view_layer.layer_collection
        )

        is_percentage = (self.mode == "PERCENTAGE")

        # Keep scene properties in sync with operator adjustments. The mode must be set
        # first so the per-mode memory properties receive the values of the active mode.
        scene.alpha_wrap_mode = self.mode
        scene.alpha_wrap_per_obj = self.per_obj
        scene.alpha_wrap_alpha = self.alpha
        scene.alpha_wrap_offset = self.offset
        scene.alpha_wrap_decimate_mod_ratio = self.decimate_mod_ratio

        tasks = []
        try:
            if not self.per_obj and len(selected_objs) > 1:
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
                    mesh_data = temp_joined.data
                    bpy.data.objects.remove(temp_joined, do_unlink=True)
                    if mesh_data and mesh_data.users == 0:
                        bpy.data.meshes.remove(mesh_data)

                target_name = (
                    (selected_objs[0].name + "_collider_alphawrap")
                    .lower()
                    .replace(".", "")
                )
                tasks.append({
                    "temp_in": temp_in,
                    "temp_out": temp_out,
                    "visual_obj_name": selected_objs[0].name,
                    "source_visual_names": [obj.name for obj in selected_objs],
                    "target_name": target_name,
                })
                # Remove any leftover individual colliders from other objects in selected_objs
                for other_obj in selected_objs[1:]:
                    other_col_name = (
                        (other_obj.name + "_collider_alphawrap")
                        .lower()
                        .replace(".", "")
                    )
                    existing_other = bpy.data.objects.get(other_col_name)
                    if existing_other:
                        other_mesh = existing_other.data
                        bpy.data.objects.remove(existing_other, do_unlink=True)
                        if other_mesh and other_mesh.users == 0:
                            bpy.data.meshes.remove(other_mesh)
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
                        "source_visual_names": [visual_obj.name],
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

        created_colliders = []
        try:
            cache_dir = os.path.join(tempfile.gettempdir(), "sdf_gen_alpha_wrap_cache")
            os.makedirs(cache_dir, exist_ok=True)

            for task in tasks:
                temp_in = task["temp_in"]
                temp_out = task["temp_out"]
                visual_obj = bpy.data.objects.get(task["visual_obj_name"])

                in_size = os.path.getsize(temp_in) if os.path.exists(temp_in) else 0
                key_str = f"{task['target_name']}_{alpha:.6f}_{offset:.6f}_{is_percentage}_{in_size}"
                cache_hash = hashlib.md5(key_str.encode("utf-8")).hexdigest()
                cached_stl = os.path.join(cache_dir, f"{cache_hash}.stl")

                if os.path.exists(cached_stl) and os.path.getsize(cached_stl) > 0:
                    shutil.copyfile(cached_stl, temp_out)
                else:
                    alpha_wrap_mesh(
                        input_path=temp_in,
                        output_path=temp_out,
                        alpha=alpha,
                        offset=offset,
                        is_percentage=is_percentage,
                    )
                    if os.path.exists(temp_out) and os.path.getsize(temp_out) > 0:
                        shutil.copyfile(temp_out, cached_stl)

                if not os.path.exists(temp_out) or os.path.getsize(temp_out) == 0:
                    continue

                collider_obj = import_stl_object(temp_out)
                setup_alpha_wrap_collider(
                    collider_obj=collider_obj,
                    visual_obj=visual_obj,
                    target_name=task["target_name"],
                    decimate_mod_ratio=self.decimate_mod_ratio,
                    source_visual_names=task.get("source_visual_names"),
                )
                created_colliders.append(collider_obj)

            # Select newly created colliders
            bpy.ops.object.select_all(action="DESELECT")
            for c in created_colliders:
                c.select_set(True)
            if created_colliders:
                bpy.context.view_layer.objects.active = created_colliders[0]

            tag_redraw_view3d()
            self.report(
                {"INFO"},
                f"Alpha wrap created {len(created_colliders)} collider(s).",
            )
            return {"FINISHED"}

        except Exception as e:
            show_message_box(
                message=f"Alpha Wrap failed: {str(e)}",
                title="Error",
                icon="ERROR",
            )
            self.report({"ERROR"}, f"Alpha Wrap failed: {str(e)}")
            return {"CANCELLED"}
        finally:
            _cleanup_task_files(tasks)


class MESH_OT_restore_alpha_wrap_defaults(bpy.types.Operator):
    bl_idname = "mesh.restore_alpha_wrap_defaults"
    bl_label = "Restore Defaults"
    bl_description = "Restores Alpha Wrap parameters to default values for the active mode"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.report({"INFO"}, "Alpha Wrap default parameters restored.")
        return {"FINISHED"}


def _install_pymeshlab_worker(state):
    """Background worker thread to install PyMeshLab via pip."""
    try:
        python_exe = get_blender_python_executable()

        cmd = [python_exe, "-m", "pip", "install", "pymeshlab"]
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        res = subprocess.run(cmd, **kwargs)

        # If system site-packages is read-only, retry with --user
        if res.returncode != 0:
            err_str = (res.stderr or "") + (res.stdout or "")
            if "PermissionError" in err_str or "Access is denied" in err_str:
                user_cmd = [python_exe, "-m", "pip", "install", "--user", "pymeshlab"]
                res = subprocess.run(user_cmd, **kwargs)

        if res.returncode != 0:
            error_output = res.stderr.strip() or res.stdout.strip() or f"Process exited with code {res.returncode}"
            state["error"] = error_output
            state["success"] = False
            return

        # Ensure user site-packages is in sys.path if pip installed there
        try:
            import site
            user_site = site.getusersitepackages()
            if user_site and os.path.exists(user_site) and user_site not in sys.path:
                sys.path.append(user_site)
        except Exception:
            pass

        import importlib
        importlib.invalidate_caches()

        # Verify import succeeds
        try:
            import pymeshlab
            state["success"] = True
        except Exception as e:
            state["error"] = f"PyMeshLab installed but could not be imported: {e}"
            state["success"] = False

    except Exception as e:
        state["error"] = str(e)
        state["success"] = False
    finally:
        state["is_done"] = True


def _create_install_timer_callback(state):
    """Timer callback function to monitor PyMeshLab installation on the main thread."""
    def timer_callback():
        wm = bpy.context.window_manager

        if not state.get("is_done", False):
            return 0.1

        if wm:
            wm.pymeshlab_installing = False
            wm.pymeshlab_install_status = ""

        tag_redraw_view3d()

        if state.get("success", False):
            show_message_box(
                message="PyMeshLab was installed successfully!\nAlpha Wrap colliders are now available.",
                title="Installation Complete",
                icon="INFO",
            )
        else:
            err = state.get("error", "Unknown error occurred.")
            show_message_box(
                message=f"Failed to install PyMeshLab:\n{err}",
                title="Installation Failed",
                icon="ERROR",
            )

        tag_redraw_view3d()
        return None

    return timer_callback


class MESH_OT_install_pymeshlab(bpy.types.Operator):
    bl_idname = "mesh.install_pymeshlab"
    bl_label = "PyMeshLab Required"
    bl_description = "Install PyMeshLab library into Blender's Python environment to enable Alpha Wrap colliders"
    bl_options = {"REGISTER", "INTERNAL"}

    def invoke(self, context, event):
        if getattr(context.window_manager, "pymeshlab_installing", False):
            self.report({"WARNING"}, "PyMeshLab installation is already in progress.")
            return {"CANCELLED"}

        if is_pymeshlab_available():
            self.report({"INFO"}, "PyMeshLab is already installed.")
            return {"CANCELLED"}

        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(
            text="PyMeshLab is required for alpha wrap collision generation.",
            icon="INFO",
        )
        col.separator()
        col.label(text="Would you like to install PyMeshLab?")

    def execute(self, context):
        wm = context.window_manager
        if getattr(wm, "pymeshlab_installing", False):
            self.report({"WARNING"}, "PyMeshLab installation is already in progress.")
            return {"CANCELLED"}

        if is_pymeshlab_available():
            self.report({"INFO"}, "PyMeshLab is already installed.")
            return {"CANCELLED"}

        wm.pymeshlab_installing = True
        wm.pymeshlab_install_status = "Installing PyMeshLab..."

        state = {
            "is_done": False,
            "success": False,
            "error": None,
        }

        thread = threading.Thread(
            target=_install_pymeshlab_worker,
            args=(state,),
            daemon=True,
        )
        thread.start()

        timer_cb = _create_install_timer_callback(state)
        bpy.app.timers.register(timer_cb, first_interval=0.1)

        tag_redraw_view3d()
        self.report({"INFO"}, "PyMeshLab installation started in background...")
        return {"FINISHED"}


