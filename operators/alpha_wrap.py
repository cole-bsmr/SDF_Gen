"""Alpha-Wrap and Planar Decimation Processor for SDF_Gen.

Contained entirely within SDF_Gen. Uses Blender's Python and PyMeshLab.
"""

import math
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple

import numpy as np


def is_pymeshlab_available() -> bool:
    """Checks whether pymeshlab can be imported in Blender's Python."""
    try:
        import pymeshlab
        return True
    except ImportError:
        return False


def _ensure_pymeshlab():
    """Checks if pymeshlab is installed in Blender's Python and imports it.

    Returns:
        The imported pymeshlab module.

    Raises:
        ImportError: If pymeshlab is not installed in Blender's Python.
    """
    try:
        import pymeshlab
        return pymeshlab
    except ImportError as e:
        raise ImportError(
            "PyMeshLab is required for Alpha Wrap. "
            "Please install it in Blender's Python via: pip install pymeshlab"
        ) from e


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


def decimate_by_planar_angle(
    vertices: np.ndarray,
    faces: np.ndarray,
    max_angle_deg: float = 5.0,
    max_passes: int = 15,
) -> Tuple[np.ndarray, np.ndarray]:
    """Decimates coplanar edges where adjacent face normal difference is below max_angle_deg."""
    cos_thr = math.cos(math.radians(max_angle_deg))
    v = np.array(vertices, dtype=np.float64, copy=True)
    f = np.array(faces, dtype=np.int64, copy=True)

    for _ in range(max_passes):
        if len(f) == 0:
            break

        # 1. Compute face normals
        v0 = v[f[:, 0]]
        v1 = v[f[:, 1]]
        v2 = v[f[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        norm = np.linalg.norm(cross, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        normals = cross / norm

        # 2. Build vertex-to-faces and edge-to-faces maps
        v_to_faces = [[] for _ in range(len(v))]
        edge_to_faces = {}
        for fi, tri in enumerate(f):
            for vi in tri:
                v_to_faces[vi].append(fi)
            for a, b in [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])]:
                edge = (min(a, b), max(a, b))
                edge_to_faces.setdefault(edge, []).append(fi)

        # 3. Find candidates where shared faces are coplanar
        candidates = []
        for (ea, eb), f_list in edge_to_faces.items():
            if len(f_list) == 2:
                n0 = normals[f_list[0]]
                n1 = normals[f_list[1]]
                dot = np.dot(n0, n1)
                if dot >= cos_thr:
                    candidates.append((ea, eb, dot))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[2], reverse=True)

        # 4. Collapse edges safely
        collapsed_map = {}
        removed_vertices = set()

        for ea, eb, _ in candidates:
            if ea in removed_vertices or eb in removed_vertices:
                continue

            valid_collapse = True
            for nfi in v_to_faces[eb]:
                tri = f[nfi]
                if ea in tri:
                    continue
                new_tri_pts = [v[ea] if vi == eb else v[vi] for vi in tri]
                new_cross = np.cross(new_tri_pts[1] - new_tri_pts[0], new_tri_pts[2] - new_tri_pts[0])
                new_norm = np.linalg.norm(new_cross)
                if new_norm < 1e-12:
                    valid_collapse = False
                    break
                new_n = new_cross / new_norm
                old_n = normals[nfi]
                if np.dot(new_n, old_n) < cos_thr:
                    valid_collapse = False
                    break

            if valid_collapse:
                collapsed_map[eb] = ea
                removed_vertices.add(eb)

        if not collapsed_map:
            break

        # Rebuild faces
        new_faces = []
        for tri in f:
            t0 = collapsed_map.get(tri[0], tri[0])
            t1 = collapsed_map.get(tri[1], tri[1])
            t2 = collapsed_map.get(tri[2], tri[2])
            if t0 != t1 and t1 != t2 and t2 != t0:
                new_faces.append([t0, t1, t2])

        f = np.array(new_faces, dtype=np.int64)

    # Compact unreferenced vertices
    used = np.unique(f)
    mapping = {old: new for new, old in enumerate(used)}
    new_v = v[used]
    final_f = np.vectorize(mapping.get)(f)

    return new_v, final_f


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
    """Wraps a 3D mesh using CGAL 3D Alpha-Wrapping with optional planar decimation."""
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

    # Prepare alpha and offset parameter values
    alpha_param = _make_filter_value(pm, alpha, is_percentage)
    offset_param = _make_filter_value(pm, offset, is_percentage)

    mode_str = f"{alpha}% / {offset}% of bbox diagonal" if is_percentage else f"alpha={alpha}, offset={offset} (absolute)"
    if verbose:
        print(f"--> Executing Alpha-Wrap ({mode_str})...")

    ms.generate_alpha_wrap(alpha=alpha_param, offset=offset_param)

    # Optional planar angle-based decimation
    if decimate_angle is not None and decimate_angle > 0.0:
        if verbose:
            print(f"--> Decimating by planar dihedral angle ({decimate_angle:.1f}° threshold)...")
        curr_m = ms.current_mesh()
        v_mat = curr_m.vertex_matrix()
        f_mat = curr_m.face_matrix()

        new_verts, new_faces = decimate_by_planar_angle(v_mat, f_mat, max_angle_deg=decimate_angle)
        new_mesh = pm.Mesh(vertex_matrix=new_verts, face_matrix=new_faces)
        ms.add_mesh(new_mesh, "angle_decimated")

    # Optional Quadric Edge Collapse decimation
    if decimate_faces is not None or decimate_perc is not None:
        qec_kwargs = {
            "preservenormal": True,
            "planarquadric": planar_quadric,
        }
        if planar_quadric:
            qec_kwargs["planarweight"] = 0.01

        if decimate_faces is not None:
            ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(decimate_faces), **qec_kwargs)
        elif decimate_perc is not None:
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
