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

        # Check if already importable via standard python paths
        found = False
        for mod_name in ["coacd", "coacd_u", "coacd_U"]:
            spec = importlib.util.find_spec(mod_name)
            if spec is not None:
                __import__(mod_name)
                found = True
                break
            else:
                sys.modules.pop(mod_name, None)

        if found:
            return True

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

        for mod_name in ["coacd", "coacd_u", "coacd_U"]:
            sys.modules.pop(mod_name, None)

        return False
    except Exception:
        for mod_name in ["coacd", "coacd_u", "coacd_U"]:
            sys.modules.pop(mod_name, None)
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
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        bm.faces.ensure_lookup_table()

        verts = np.array([v.co for v in bm.verts], dtype=np.float64)
        faces = np.array(
            [[v.index for v in f.verts] for f in bm.faces], dtype=np.int32
        )
        bm.free()
    finally:
        eval_obj.to_mesh_clear()

    return verts, faces


_COACD_DECOMPOSITION_CACHE = {}


def fallback_convex_hull(verts: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generates a single watertight convex hull as a safe fallback when decomposition fails."""
    if len(verts) < 4:
        return []
    try:
        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        res = bmesh.ops.convex_hull(bm, input=bm.verts)
        unused_geom = list(set(res.get("geom_unused", [])) | set(res.get("geom_interior", [])))
        if unused_geom:
            bmesh.ops.delete(bm, geom=unused_geom, context="VERTS")
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()
        bm.faces.ensure_lookup_table()
        ch_verts = np.array([v.co for v in bm.verts], dtype=np.float64)
        ch_faces = np.array([[v.index for v in f.verts] for f in bm.faces], dtype=np.int32)
        bm.free()
        if len(ch_verts) >= 4 and len(ch_faces) >= 4:
            return [(ch_verts, ch_faces)]
    except Exception as e:
        print(f"[SDF_Gen] Fallback convex hull failed: {e}")
    return []


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
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Runs CoACD on a visual object and returns a list of (vertices, faces) for each part."""
    coacd = get_coacd_module()

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

    if hasattr(coacd, "set_log_level"):
        try:
            coacd.set_log_level("warn")
        except Exception:
            pass

    max_ch = max_convex_hull if max_convex_hull > 0 else -1
    safe_thresh = max(0.01, float(threshold))

    try:
        coacd_mesh = coacd.Mesh(verts, faces)
        parts = coacd.run_coacd(
            coacd_mesh,
            threshold=safe_thresh,
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
    except Exception as ex:
        print(
            f"[SDF_Gen] CoACD decomposition failed with preprocess='{preprocess_mode}': {ex}. "
            "Retrying with preprocess='on'..."
        )
        try:
            coacd_mesh = coacd.Mesh(verts, faces)
            parts = coacd.run_coacd(
                coacd_mesh,
                threshold=max(0.02, safe_thresh),
                max_convex_hull=int(max_ch),
                preprocess_mode="on",
                preprocess_resolution=int(preprocess_resolution),
                mcts_iterations=int(mcts_iterations),
                mcts_max_depth=int(mcts_max_depth),
                mcts_nodes=int(mcts_nodes),
                merge=merge,
                decimate=decimate,
                max_ch_vertex=int(max_ch_vertex),
            )
        except Exception as ex2:
            print(f"[SDF_Gen] CoACD retry failed ({ex2}). Generating robust convex hull fallback.")
            parts = fallback_convex_hull(verts)

    _COACD_DECOMPOSITION_CACHE[cache_key] = parts
    return parts
