"""Alpha-Wrap and Planar Decimation Processor for SDF_Gen.

Contained entirely within SDF_Gen. Uses Blender's Python and PyMeshLab.
"""

import os
import sys
import time
from typing import Any, Dict, Optional


def get_blender_python_executable() -> str:
    """Finds the Python executable for the current Blender instance across platforms."""
    # 1. If sys.executable is already a python executable
    exe = sys.executable
    if exe and os.path.basename(exe).lower().startswith("python"):
        return exe

    # 2. Look inside Blender's python directory (sys.prefix)
    prefix = sys.prefix
    candidates = []
    if sys.platform == "win32":
        candidates.extend([
            os.path.join(prefix, "bin", "python.exe"),
            os.path.join(prefix, "python.exe"),
        ])
    else:
        candidates.extend([
            os.path.join(prefix, "bin", "python3"),
            os.path.join(prefix, "bin", "python"),
        ])

    for c in candidates:
        if os.path.isfile(c):
            return c

    return exe or "python"


def is_pymeshlab_available() -> bool:
    """Checks whether pymeshlab can be imported in Blender's Python."""
    try:
        import site
        import importlib
        import importlib.util
        user_site = site.getusersitepackages()
        if user_site and os.path.exists(user_site) and user_site not in sys.path:
            sys.path.append(user_site)
        importlib.invalidate_caches()
        spec = importlib.util.find_spec("pymeshlab")
        if spec is None:
            sys.modules.pop("pymeshlab", None)
            return False
        import pymeshlab
        return True
    except Exception:
        sys.modules.pop("pymeshlab", None)
        return False


def _ensure_pymeshlab():
    """Checks if pymeshlab is installed in Blender's Python and imports it.

    Returns:
        The imported pymeshlab module.

    Raises:
        ImportError: If pymeshlab is not installed in Blender's Python.
    """
    if is_pymeshlab_available():
        import pymeshlab
        return pymeshlab

    raise ImportError(
        "PyMeshLab is required for Alpha Wrap. "
        "Please click 'Install PyMeshLab' in the Colliders panel or install via: "
        f"{get_blender_python_executable()} -m pip install pymeshlab"
    )


def _make_filter_value(ml_module: Any, value: float, is_percentage: bool) -> Any:
    """Wraps a numerical value in PyMeshLab's PercentageValue or PureValue if available."""
    if is_percentage:
        if hasattr(ml_module, "PercentageValue"):
            return ml_module.PercentageValue(value)
        elif hasattr(ml_module, "Percentage"):
            return ml_module.Percentage(value)
    else:
        if hasattr(ml_module, "PureValue"):
            return ml_module.PureValue(value)
        elif hasattr(ml_module, "AbsoluteValue"):
            return ml_module.AbsoluteValue(value)
    return value


def get_mesh_stats(mesh_set: Any) -> Dict[str, Any]:
    """Extracts geometric and topological statistics from the current mesh."""
    mesh = mesh_set.current_mesh()
    bbox = mesh.bounding_box()
    min_pt = bbox.min()
    max_pt = bbox.max()
    extents = max_pt - min_pt
    diagonal = bbox.diagonal()

    return {
        "vertex_count": mesh.vertex_number(),
        "face_count": mesh.face_number(),
        "bbox_min": min_pt,
        "bbox_max": max_pt,
        "extents": extents,
        "diagonal": diagonal,
    }



def alpha_wrap_mesh(
    input_path: str,
    output_path: Optional[str] = None,
    alpha: float = 2.0,
    offset: float = 0.5,
    is_percentage: bool = True,
    decimate_faces: Optional[int] = None,
    decimate_perc: Optional[float] = None,
    decimate_angle: Optional[float] = None,
    planar_quadric: bool = False,
    clean_mesh: bool = True,
    recompute_normals: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Wraps a 3D mesh using CGAL 3D Alpha-Wrapping."""
    # CGAL 3D Alpha Wrapping strictly requires alpha > 0 and offset > 0.
    if alpha <= 0.0:
        raise ValueError(
            f"Alpha must be strictly positive (> 0) as required by CGAL, got {alpha}."
        )
    if offset <= 0.0:
        raise ValueError(
            f"Offset must be strictly positive (> 0) as required by CGAL, got {offset}."
        )

    pm = _ensure_pymeshlab()

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input mesh file not found: {input_path}")

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_wrapped{ext}"

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    start_time = time.time()
    ms = pm.MeshSet()

    if verbose:
        print(f"--> Loading input mesh: {input_path}")
    ms.load_new_mesh(input_path)

    initial_stats = get_mesh_stats(ms)
    diagonal = initial_stats.get("diagonal", 0.0)

    if is_percentage:
        alpha = max(alpha, 0.5)
        offset = max(offset, 0.01)
    elif diagonal > 0.0:
        alpha = max(alpha, diagonal * 0.005)
        offset = max(offset, diagonal * 0.0001)

    alpha_param = _make_filter_value(pm, alpha, is_percentage)
    offset_param = _make_filter_value(pm, offset, is_percentage)

    mode_str = f"{alpha}% / {offset}% of bbox diagonal" if is_percentage else f"alpha={alpha}, offset={offset} (absolute)"
    if verbose:
        print(f"--> Executing Alpha-Wrap ({mode_str})...")

    ms.generate_alpha_wrap(alpha=alpha_param, offset=offset_param)

    if ms.current_mesh().face_number() == 0:
        raise RuntimeError(
            "Alpha wrap produced an empty mesh. Please ensure the input mesh "
            "contains valid 3D geometry and Alpha/Offset parameters are sufficiently large."
        )

    # Optional Quadric Edge Collapse decimation
    if (decimate_faces is not None and int(decimate_faces) > 0) or (decimate_perc is not None and float(decimate_perc) > 0.0):
        qec_kwargs = {
            "preservenormal": True,
            "planarquadric": planar_quadric,
        }
        if planar_quadric:
            qec_kwargs["planarweight"] = 0.01

        if decimate_faces is not None and int(decimate_faces) > 0:
            ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(decimate_faces), **qec_kwargs)
        elif decimate_perc is not None and float(decimate_perc) > 0.0:
            ms.meshing_decimation_quadric_edge_collapse(targetperc=float(decimate_perc), **qec_kwargs)

    # Optional cleaning and repair
    if clean_mesh:
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_duplicate_vertices()
        ms.meshing_remove_unreferenced_vertices()

    if recompute_normals:
        ms.compute_normal_per_vertex()

    final_stats = get_mesh_stats(ms)

    if verbose:
        print(f"--> Saving output mesh: {output_path}")
    ms.save_current_mesh(output_path)

    elapsed = time.time() - start_time
    return {
        "input_path": input_path,
        "output_path": output_path,
        "elapsed_seconds": elapsed,
        "initial_stats": initial_stats,
        "final_stats": final_stats,
    }
