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

