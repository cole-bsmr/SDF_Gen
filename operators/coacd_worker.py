"""CoACD (Collision-Aware Approximate Convex Decomposition) Processor for SDF_Gen.

Contained within SDF_Gen. Uses Blender's Python and CoACD.
"""

import os
import sys
import platform
import glob
import zipfile
import tempfile
import shutil
import atexit
import subprocess
from typing import List, Tuple, Any, Optional
import numpy as np
import bpy
import bmesh
import mathutils

from .alpha_wrap import get_blender_python_executable

_EXTRACTED_WHEEL_DIRS = []


def _cleanup_extracted_wheels():
    for p in _EXTRACTED_WHEEL_DIRS:
        if os.path.exists(p):
            try:
                shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass


atexit.register(_cleanup_extracted_wheels)


def _try_load_wheel_from_dir(package_name: str, wheels_dir: str) -> bool:
    """Extracts and adds a matching wheel to sys.path if found in wheels_dir."""
    if not os.path.isdir(wheels_dir):
        return False

    system = platform.system().lower()
    machine = platform.machine().lower()

    platform_tags = []
    if system == "windows":
        platform_tags = ["win_amd64"]
    elif system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            platform_tags = ["macosx", "arm64"]
        else:
            platform_tags = ["macosx", "x86_64"]
    elif system == "linux":
        if "aarch64" in machine or "arm64" in machine:
            platform_tags = ["manylinux", "aarch64"]
        else:
            platform_tags = ["manylinux", "x86_64"]
    else:
        return False

    candidates = glob.glob(os.path.join(wheels_dir, f"{package_name}-*.whl"))
    for whl in candidates:
        name = os.path.basename(whl).lower()
        if all(tag in name for tag in platform_tags):
            try:
                temp_dir = tempfile.mkdtemp(prefix=f"{package_name}_whl_")
                _EXTRACTED_WHEEL_DIRS.append(temp_dir)
                with zipfile.ZipFile(whl, "r") as zf:
                    zf.extractall(temp_dir)
                if temp_dir not in sys.path:
                    sys.path.insert(0, temp_dir)
                return True
            except Exception as e:
                print(f"[SDF_Gen] Failed to extract wheel {whl}: {e}")
                return False
    return False


def is_coacd_available() -> bool:
    """Checks whether coacd (or coacd_u) can be imported in Blender's Python."""
    try:
        import site
        import importlib
        import importlib.util

        user_site = site.getusersitepackages()
        if user_site and os.path.exists(user_site) and user_site not in sys.path:
            sys.path.append(user_site)
        importlib.invalidate_caches()

        # Check if already in sys.modules or importable via standard python paths
        for mod_name in ["coacd", "coacd_u", "coacd_U"]:
            spec = importlib.util.find_spec(mod_name)
            if spec is not None:
                __import__(mod_name)
                return True

        # Check known extension wheels location if user has coacd_collision_gen extension installed
        blender_user_ext = os.path.join(
            bpy.utils.resource_path("USER"),
            "extensions",
            "user_default",
            "coacd_collision_gen",
            "wheels",
        )
        if os.path.isdir(blender_user_ext):
            if _try_load_wheel_from_dir("coacd_u", blender_user_ext):
                importlib.invalidate_caches()
                try:
                    import coacd_u

                    return True
                except Exception:
                    pass

        # Check local addon wheels dir if bundled
        addon_wheels = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "wheels"
        )
        if os.path.isdir(addon_wheels):
            if _try_load_wheel_from_dir(
                "coacd_u", addon_wheels
            ) or _try_load_wheel_from_dir("coacd", addon_wheels):
                importlib.invalidate_caches()
                try:
                    import coacd_u

                    return True
                except Exception:
                    try:
                        import coacd

                        return True
                    except Exception:
                        pass

        return False
    except Exception:
        return False


def get_coacd_module():
    """Returns the available coacd module or raises ImportError."""
    if not is_coacd_available():
        raise ImportError(
            "CoACD is required for Convex Decomposition. "
            "Please click 'Install CoACD' in the Colliders panel or install via: "
            f"{get_blender_python_executable()} -m pip install coacd"
        )
    for mod_name in ["coacd", "coacd_u", "coacd_U"]:
        if mod_name in sys.modules:
            return sys.modules[mod_name]
        try:
            return __import__(mod_name)
        except ImportError:
            continue
    raise ImportError("Failed to load CoACD module.")


def _install_coacd_worker(state):
    """Background worker thread to install CoACD via pip."""
    try:
        python_exe = get_blender_python_executable()

        cmd = [python_exe, "-m", "pip", "install", "coacd"]
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        res = subprocess.run(cmd, **kwargs)

        if res.returncode != 0:
            err_str = (res.stderr or "") + (res.stdout or "")
            if (
                "PermissionError" in err_str
                or "Access is denied" in err_str
                or "read-only" in err_str.lower()
            ):
                user_cmd = [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--user",
                    "coacd",
                ]
                res = subprocess.run(user_cmd, **kwargs)

        if res.returncode != 0:
            error_output = (
                res.stderr.strip()
                or res.stdout.strip()
                or f"Process exited with code {res.returncode}"
            )
            state["error"] = error_output
            state["success"] = False
            return

        try:
            import site

            user_site = site.getusersitepackages()
            if (
                user_site
                and os.path.exists(user_site)
                and user_site not in sys.path
            ):
                sys.path.append(user_site)
        except Exception:
            pass

        import importlib

        importlib.invalidate_caches()

        if is_coacd_available():
            state["success"] = True
        else:
            state["error"] = "CoACD was installed but could not be imported."
            state["success"] = False

    except Exception as e:
        state["error"] = str(e)
        state["success"] = False
    finally:
        state["is_done"] = True


def extract_mesh_data_from_object(
    obj: bpy.types.Object,
) -> Tuple[np.ndarray, np.ndarray]:
    """Extracts triangulated vertices and face indices in object local coordinates."""
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)

        verts = np.array([v.co for v in bm.verts], dtype=np.float64)
        faces = np.array(
            [[v.index for v in f.verts] for f in bm.faces], dtype=np.int32
        )
        bm.free()
    finally:
        eval_obj.to_mesh_clear()

    return verts, faces


def extract_combined_mesh_data(
    objects: List[bpy.types.Object], reference_obj: bpy.types.Object
) -> Tuple[np.ndarray, np.ndarray]:
    """Combines meshes of multiple objects into reference_obj's local coordinate system."""
    all_verts = []
    all_faces = []
    vert_offset = 0

    dg = bpy.context.evaluated_depsgraph_get()
    ref_inv = reference_obj.matrix_world.inverted()

    for obj in objects:
        if obj.type != "MESH":
            continue
        eval_obj = obj.evaluated_get(dg)
        mesh = eval_obj.to_mesh()
        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            obj_to_ref = ref_inv @ obj.matrix_world
            for v in bm.verts:
                co = obj_to_ref @ v.co
                all_verts.append((co.x, co.y, co.z))
            for f in bm.faces:
                all_faces.append([v.index + vert_offset for v in f.verts])
            vert_offset += len(bm.verts)
            bm.free()
        finally:
            eval_obj.to_mesh_clear()

    if not all_verts or not all_faces:
        return np.empty((0, 3), dtype=np.float64), np.empty((0, 3), dtype=np.int32)

    return np.array(all_verts, dtype=np.float64), np.array(all_faces, dtype=np.int32)


_COACD_DECOMPOSITION_CACHE = {}


def run_coacd_decomposition(
    visual_obj: bpy.types.Object,
    threshold: float = 0.05,
    max_convex_hull: int = 16,
    preprocess_mode: str = "auto",
    preprocess_resolution: int = 50,
    mcts_iterations: int = 150,
    mcts_max_depth: int = 3,
    mcts_nodes: int = 20,
    merge: bool = True,
    decimate: bool = False,
    max_ch_vertex: int = 256,
    combined_objects: Optional[List[bpy.types.Object]] = None,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Runs CoACD on a visual object (or combined objects) and returns a list of (vertices, faces) for each part."""
    coacd = get_coacd_module()

    if combined_objects and len(combined_objects) > 1:
        verts, faces = extract_combined_mesh_data(combined_objects, visual_obj)
        cache_id = "_".join(sorted(o.name for o in combined_objects))
    else:
        verts, faces = extract_mesh_data_from_object(visual_obj)
        cache_id = visual_obj.name

    if len(verts) == 0 or len(faces) == 0:
        raise ValueError(
            f"Object '{visual_obj.name}' has no mesh geometry to decompose."
        )

    cache_key = (
        cache_id,
        round(float(threshold), 4),
        int(max_convex_hull),
        preprocess_mode.lower(),
        int(preprocess_resolution),
        int(mcts_iterations),
        int(mcts_max_depth),
        int(mcts_nodes),
        merge,
        decimate,
        int(max_ch_vertex),
        len(verts),
        len(faces),
    )

    if cache_key in _COACD_DECOMPOSITION_CACHE:
        return _COACD_DECOMPOSITION_CACHE[cache_key]

    coacd_mesh = coacd.Mesh(verts, faces)

    if hasattr(coacd, "set_log_level"):
        try:
            coacd.set_log_level("warn")
        except Exception:
            pass

    max_ch = max_convex_hull if max_convex_hull > 0 else -1

    parts = coacd.run_coacd(
        coacd_mesh,
        threshold=float(threshold),
        max_convex_hull=int(max_ch),
        preprocess_mode=preprocess_mode.lower(),
        preprocess_resolution=int(preprocess_resolution),
        mcts_iterations=int(mcts_iterations),
        mcts_max_depth=int(mcts_max_depth),
        mcts_nodes=int(mcts_nodes),
        merge=merge,
        decimate=decimate,
        max_ch_vertex=int(max_ch_vertex),
    )

    _COACD_DECOMPOSITION_CACHE[cache_key] = parts
    return parts


def partition_mesh_with_detail_boxes(
    visual_obj: bpy.types.Object,
    detail_boxes: List[bpy.types.Object],
    default_threshold: float = 0.05,
    default_max_convex_hull: int = 16,
) -> List[Tuple[str, np.ndarray, np.ndarray, float, int]]:
    """Partitions visual_obj using one or more detail_boxes via Boolean operations.

    Returns a list of tuples: (zone_name, verts, faces, threshold, max_hulls)
    All vertices are in visual_obj's local coordinate system.
    """
    dg = bpy.context.evaluated_depsgraph_get()

    available_solvers = [
        item.identifier
        for item in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items
    ]
    solver = (
        "EXACT"
        if "EXACT" in available_solvers
        else (
            "MANIFOLD"
            if "MANIFOLD" in available_solvers
            else ("FAST" if "FAST" in available_solvers else "FLOAT")
        )
    )

    target_col = (
        visual_obj.users_collection[0]
        if visual_obj.users_collection
        else bpy.context.scene.collection
    )

    temp_objects = []
    temp_meshes = []

    def cleanup():
        for o in temp_objects:
            for col in list(o.users_collection):
                col.objects.unlink(o)
            bpy.data.objects.remove(o, do_unlink=True)
        for m in temp_meshes:
            if m.users == 0:
                bpy.data.meshes.remove(m)

    zones = []

    try:
        # Create temporary world-space mesh for visual_obj
        eval_vis = visual_obj.evaluated_get(dg)
        base_mesh = bpy.data.meshes.new_from_object(eval_vis)
        base_mesh.transform(visual_obj.matrix_world)
        temp_meshes.append(base_mesh)

        current_body_obj = bpy.data.objects.new("temp_current_body", base_mesh)
        target_col.objects.link(current_body_obj)
        temp_objects.append(current_body_obj)

        inv_ref_mat = visual_obj.matrix_world.inverted()

        for idx, box_obj in enumerate(detail_boxes):
            if not box_obj or box_obj.type != "MESH":
                continue

            # Create temporary world-space copy of detail box
            eval_box = box_obj.evaluated_get(dg)
            box_mesh = bpy.data.meshes.new_from_object(eval_box)
            box_mesh.transform(box_obj.matrix_world)

            # Ensure proper outward normals even if user mirrored or negative-scaled the box
            bm_box = bmesh.new()
            bm_box.from_mesh(box_mesh)
            bmesh.ops.recalc_face_normals(bm_box, faces=bm_box.faces)
            bm_box.to_mesh(box_mesh)
            bm_box.free()

            temp_meshes.append(box_mesh)

            temp_box_obj = bpy.data.objects.new(f"temp_box_{idx}", box_mesh)
            target_col.objects.link(temp_box_obj)
            temp_objects.append(temp_box_obj)

            # 1. Carve inside chunk (intersection of current_body with this box)
            inside_mesh = current_body_obj.data.copy()
            temp_meshes.append(inside_mesh)
            inside_obj = bpy.data.objects.new(f"temp_inside_{idx}", inside_mesh)
            target_col.objects.link(inside_obj)
            temp_objects.append(inside_obj)

            mod_in = inside_obj.modifiers.new("Intersect", "BOOLEAN")
            mod_in.operation = "INTERSECT"
            mod_in.object = temp_box_obj
            mod_in.solver = solver

            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()

            eval_in = inside_obj.evaluated_get(dg)
            m_in = eval_in.to_mesh()
            try:
                # Validate that m_in is a genuine intersection inside the box
                # and not a silent failed pass-through of the entire mesh
                is_valid_inside = False
                if len(m_in.vertices) > 0 and len(m_in.polygons) > 0:
                    if (
                        len(m_in.vertices) == len(current_body_obj.data.vertices)
                        and len(m_in.polygons) == len(current_body_obj.data.polygons)
                    ):
                        is_valid_inside = False
                    else:
                        box_inv = box_obj.matrix_world.inverted()
                        xs = [c[0] for c in box_obj.bound_box]
                        ys = [c[1] for c in box_obj.bound_box]
                        zs = [c[2] for c in box_obj.bound_box]
                        min_x, max_x = min(xs), max(xs)
                        min_y, max_y = min(ys), max(ys)
                        min_z, max_z = min(zs), max(zs)
                        dx = max_x - min_x
                        dy = max_y - min_y
                        dz = max_z - min_z
                        tol_x = dx * 0.1 + 1e-4
                        tol_y = dy * 0.1 + 1e-4
                        tol_z = dz * 0.1 + 1e-4
                        outside = 0
                        for v in m_in.vertices:
                            p = box_inv @ v.co
                            if (
                                p.x < min_x - tol_x
                                or p.x > max_x + tol_x
                                or p.y < min_y - tol_y
                                or p.y > max_y + tol_y
                                or p.z < min_z - tol_z
                                or p.z > max_z + tol_z
                            ):
                                outside += 1
                        if (outside / len(m_in.vertices)) < 0.05:
                            is_valid_inside = True

                if is_valid_inside:
                    bm = bmesh.new()
                    bm.from_mesh(m_in)
                    bmesh.ops.triangulate(bm, faces=bm.faces)
                    verts = np.array(
                        [(inv_ref_mat @ v.co) for v in bm.verts],
                        dtype=np.float64,
                    )
                    faces = np.array(
                        [[v.index for v in f.verts] for f in bm.faces],
                        dtype=np.int32,
                    )
                    thresh = getattr(box_obj, "detail_threshold", default_threshold)
                    max_hulls = getattr(
                        box_obj, "detail_max_convex_hull", default_max_convex_hull
                    )
                    zones.append(
                        (f"detail_{idx}", verts, faces, thresh, max_hulls)
                    )
                    bm.free()
                else:
                    print(
                        f"[SDF_Gen] Warning: Boolean intersection on detail box '{box_obj.name}' "
                        f"did not find an interior volume; skipping detail zone."
                    )
            finally:
                eval_in.to_mesh_clear()

            # 2. Subtract box from current body
            mod_out = current_body_obj.modifiers.new(
                f"Diff_{idx}", "BOOLEAN"
            )
            mod_out.operation = "DIFFERENCE"
            mod_out.object = temp_box_obj
            mod_out.solver = solver

            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()

            eval_curr = current_body_obj.evaluated_get(dg)
            new_body_mesh = bpy.data.meshes.new_from_object(eval_curr)
            temp_meshes.append(new_body_mesh)
            current_body_obj.modifiers.clear()
            old_mesh = current_body_obj.data
            current_body_obj.data = new_body_mesh
            if old_mesh in temp_meshes:
                temp_meshes.remove(old_mesh)
            bpy.data.meshes.remove(old_mesh)
            eval_curr.to_mesh_clear()
            bpy.context.view_layer.update()

        # 3. Remaining outside body
        dg = bpy.context.evaluated_depsgraph_get()
        eval_rem = current_body_obj.evaluated_get(dg)
        m_rem = eval_rem.to_mesh()
        try:
            bm = bmesh.new()
            bm.from_mesh(m_rem)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            if len(bm.verts) > 0 and len(bm.faces) > 0:
                verts = np.array(
                    [(inv_ref_mat @ v.co) for v in bm.verts],
                    dtype=np.float64,
                )
                faces = np.array(
                    [[v.index for v in f.verts] for f in bm.faces],
                    dtype=np.int32,
                )
                zones.append(
                    ("base", verts, faces, default_threshold, default_max_convex_hull)
                )
            bm.free()
        finally:
            eval_rem.to_mesh_clear()

    finally:
        cleanup()

    return zones


def run_coacd_decomposition_multi_zone(
    visual_obj: bpy.types.Object,
    detail_boxes: List[bpy.types.Object],
    default_threshold: float = 0.05,
    default_max_convex_hull: int = 16,
    preprocess_mode: str = "auto",
    preprocess_resolution: int = 50,
    mcts_iterations: int = 150,
    mcts_max_depth: int = 3,
    mcts_nodes: int = 20,
    merge: bool = True,
    decimate: bool = False,
    max_ch_vertex: int = 256,
) -> List[Tuple[str, np.ndarray, np.ndarray]]:
    """Runs CoACD on visual_obj partitioned with detail_boxes.

    Returns a list of (part_identifier, verts, faces) in visual_obj's local coordinates.
    """
    coacd = get_coacd_module()
    if hasattr(coacd, "set_log_level"):
        try:
            coacd.set_log_level("warn")
        except Exception:
            pass

    if not detail_boxes:
        parts = run_coacd_decomposition(
            visual_obj=visual_obj,
            threshold=default_threshold,
            max_convex_hull=default_max_convex_hull,
            preprocess_mode=preprocess_mode,
            preprocess_resolution=preprocess_resolution,
            mcts_iterations=mcts_iterations,
            mcts_max_depth=mcts_max_depth,
            mcts_nodes=mcts_nodes,
            merge=merge,
            decimate=decimate,
            max_ch_vertex=max_ch_vertex,
        )
        return [(f"part_{i}", v, f) for i, (v, f) in enumerate(parts)]

    zones = partition_mesh_with_detail_boxes(
        visual_obj=visual_obj,
        detail_boxes=detail_boxes,
        default_threshold=default_threshold,
        default_max_convex_hull=default_max_convex_hull,
    )

    if not zones:
        parts = run_coacd_decomposition(
            visual_obj=visual_obj,
            threshold=default_threshold,
            max_convex_hull=default_max_convex_hull,
            preprocess_mode=preprocess_mode,
            preprocess_resolution=preprocess_resolution,
            mcts_iterations=mcts_iterations,
            mcts_max_depth=mcts_max_depth,
            mcts_nodes=mcts_nodes,
            merge=merge,
            decimate=decimate,
            max_ch_vertex=max_ch_vertex,
        )
        return [(f"part_{i}", v, f) for i, (v, f) in enumerate(parts)]

    all_parts = []
    for zone_name, verts, faces, thresh, max_hulls in zones:
        if len(verts) == 0 or len(faces) == 0:
            continue
        coacd_mesh = coacd.Mesh(verts, faces)
        max_ch = max_hulls if max_hulls > 0 else -1
        zone_parts = coacd.run_coacd(
            coacd_mesh,
            threshold=float(thresh),
            max_convex_hull=int(max_ch),
            preprocess_mode=preprocess_mode.lower(),
            preprocess_resolution=int(preprocess_resolution),
            mcts_iterations=int(mcts_iterations),
            mcts_max_depth=int(mcts_max_depth),
            mcts_nodes=int(mcts_nodes),
            merge=merge,
            decimate=decimate,
            max_ch_vertex=int(max_ch_vertex),
        )
        for part_idx, (p_verts, p_faces) in enumerate(zone_parts):
            all_parts.append((f"{zone_name}_part_{part_idx}", p_verts, p_faces))

    return all_parts

