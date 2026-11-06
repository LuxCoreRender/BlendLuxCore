from contextlib import contextmanager
from time import time
import os
import re
import numpy as np
import pyluxcore

_needs_reload = "bpy" in locals()

import bpy

from . import caches
from .. import utils
from ..utils.errorlog import LuxCoreErrorLog

if _needs_reload:
    import importlib

    importlib.reload(caches)
    importlib.reload(utils)


# https://blenderartists.org/t/\
# efficient-copying-of-vertex-coords-to-and-from-numpy-arrays/661467/2
def get_ndarray(
    bpy_collection: bpy.types.bpy_prop_collection,
    attr: str,
    stride: int,
    dtype: np.dtype,
):
    """Get a numpy array from a Blender collection.

    If stride == 0, the array is raveled
    """
    count = len(bpy_collection)
    buffer = np.empty(shape=(count, stride if stride else 1), dtype=dtype)
    bpy_collection.foreach_get(attr, np.ravel(buffer))
    if not stride:
        buffer = buffer.ravel()
    return buffer


def convert(
    obj,
    mesh_key,
    depsgraph,
    luxcore_scene,
    is_viewport_render,
    use_instancing,
    transform,
    exporter=None,
):
    start_time = time()

    use_proxy = (
        hasattr(obj.luxcore, "use_proxy")
        and obj.luxcore.use_proxy
        and obj.luxcore.scene_shape != ""
    )

    if use_proxy:
        # library= makes relative ("//...") proxy paths resolve against the .blend file
        # obj was linked from, not whichever file currently has it open - otherwise a
        # linked object's proxy would only be found in the file that originally created it.
        ply_path = bpy.path.abspath(obj.luxcore.scene_shape, library=obj.original.library)

        if not os.path.exists(ply_path):
            LuxCoreErrorLog.add_warning(
                f"Proxy PLY file not found, falling back to exporting the Blender mesh: {ply_path}",
                obj_name=obj.name,
            )
            use_proxy = False

    if use_proxy:
        # If the given file ends in a numeric suffix (e.g. "tree007.ply"), treat it as
        # one part of a multi-material proxy: LuxCore's filesaver ("Only write LuxCore
        # scene") splits a multi-material mesh into one PLY per used material index,
        # using exactly this naming scheme. We auto-discover the sibling files so the
        # user only has to point at one of them, instead of listing every material by hand.
        # The suffix is always exactly 3 digits (material index, zero padded). Matching more
        # would swallow digits belonging to the object name, e.g. "Cube.006" + "001" is
        # "Cube.006001" and must give material index 1, not 6001.
        directory, filename = os.path.split(ply_path)
        match = re.match(r"^(.*?)(\d{3})(\.ply)$", filename, re.IGNORECASE)

        parts = {}
        if match:
            base_name, _, ext = match.groups()
            sibling_pattern = re.compile(
                rf"^{re.escape(base_name)}(\d{{3}}){re.escape(ext)}$", re.IGNORECASE
            )
            for entry in os.listdir(directory):
                entry_match = sibling_pattern.match(entry)
                if entry_match:
                    mat_index = int(entry_match.group(1))
                    parts[mat_index] = os.path.join(directory, entry)
        else:
            # No numeric suffix found, fall back to a single-material proxy
            parts[0] = ply_path

        scene_props = pyluxcore.Properties()
        mesh_definitions = []
        for mat_index, part_path in sorted(parts.items()):
            shape_key = f"{mesh_key}_{mat_index:03d}"
            prefix = "scene.shapes." + shape_key + "."
            scene_props.Set(pyluxcore.Property(prefix + "type", "mesh"))
            scene_props.Set(pyluxcore.Property(prefix + "ply", part_path))
            mesh_definitions.append((shape_key, mat_index))

        luxcore_scene.Parse(scene_props)

        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += time() - start_time

        return caches.exported_data.ExportedMesh(mesh_definitions)

    with _prepare_mesh(obj, depsgraph) as mesh:
        if mesh is None:
            return None

        # Blender API may not be always consistent with naming, for the mesh object.
        # For the sake of clarity, we list here our naming conventions.
        # They may specially differ from attribute domains...
        # https://docs.blender.org/api/current/bpy_types_enum_items/attribute_domain_items.html#rna-enum-attribute-domain-items
        # Point: a point in the 3D-space, (float, float, float)
        # Vertex: an index to the mesh array of points
        # Loop: a vertex and an edge

        # Loop vertices
        loop_vertices = get_ndarray(mesh.loops, "vertex_index", 0, np.uint32)

        # Points
        vertex_points = get_ndarray(mesh.vertices, "co", 3, np.float32)
        loop_points = vertex_points[loop_vertices]

        # Normals
        vertex_normals = get_ndarray(mesh.vertices, "normal", 3, np.float32)
        loop_normals = vertex_normals[loop_vertices]

        # Triangle loop indices
        triangle_loops = get_ndarray(
            mesh.loop_triangles, "loops", 3, np.uint32
        )

        # Material slot index for each triangle
        loop_triangle_materials = get_ndarray(
            mesh.loop_triangles, "material_index", 1, np.uint32
        ).ravel()
        unique_mats = np.unique(loop_triangle_materials)

        # UV
        uvs = [
            get_ndarray(uv_layer.uv, "vector", 2, np.float32)
            for uv_layer in mesh.uv_layers
        ]

        # Vertex colors
        def reshape_colors(colors, domain):
            if domain == "POINT":
                return colors[loop_vertices]
            elif domain == "CORNER":
                return colors
            else:
                raise ValueError(f"Unhandled attribute domain: '{domain}'")

        rgba_colors = [
            reshape_colors(
                get_ndarray(attribute.data, "color", 4, np.float32),
                attribute.domain,
            )
            for attribute in mesh.color_attributes
        ]
        rgb = [rgba[:, :3] for rgba in rgba_colors]
        alphas = [rgba[:, 3] for rgba in rgba_colors]

        # Transformation
        if is_viewport_render or use_instancing:
            mesh_transform = None
        else:
            mesh_transform = np.array(
                [
                    transform[0][0:4],
                    transform[1][0:4],
                    transform[2][0:4],
                    transform[3][0:4],
                ],
                dtype=np.float32,
            )

        # Log
        def fmt_layer(layers, layer_name):
            nlayers = len(layers)
            suffix = "layers" if nlayers > 1 else "layer"
            return f"{nlayers} {layer_name} {suffix}"
        print(f"[BLC] Exporting '{str(mesh_key)}' - {len(unique_mats)} submesh(es)")
        print(f"[BLC] - {len(loop_points)} points")
        print(f"[BLC] - {len(loop_normals)} normals")
        print(f"[BLC] - {fmt_layer(uvs, 'uv')}")
        print(f"[BLC] - {fmt_layer(rgb, 'color')}")
        print(f"[BLC] - {fmt_layer(alphas, 'alpha')}")

        mesh_definitions = []
        for mat in unique_mats:
            mat_triangles = triangle_loops[loop_triangle_materials == mat]
            name = f"{str(mesh_key)}{mat:03d}"


            print(f"[BLC] - Submesh #{mat:03d}: {len(mat_triangles)} triangles")

            luxcore_scene.DefineMeshExt(
                name=name,
                points=loop_points,
                triangles=mat_triangles,
                normals=loop_normals,
                uvs=uvs,
                colors=rgb,
                alphas=alphas,
                transformation=mesh_transform,
            )
            mesh_definitions.append((name, mat))

        duration = time() - start_time
        if exporter and exporter.stats:
            exporter.stats.export_time_meshes.value += duration
        print(f"[BLC] Export duration: {duration:.3f}s")
        print("[BLC]")

        return caches.exported_data.ExportedMesh(mesh_definitions)


@contextmanager
def _prepare_mesh(obj, depsgraph):
    """
    Create a temporary mesh from an object.
    The mesh is guaranteed to be removed when the calling block ends.
    Can return None if no mesh could be created from the object (e.g. for empties)

    Use it like this:

    with mesh_converter.convert(obj, depsgraph) as mesh:
        if mesh:
            print(mesh.name)
            ...
    """

    mesh = None
    object_eval = None

    try:
        object_eval = obj.evaluated_get(depsgraph)
        if object_eval:
            mesh = object_eval.to_mesh()

            if mesh:
                # TODO test if this makes sense
                # has been tested briefly for_v2.10. Seems to work, also
                # including custom normals now
                ## but leaving this out on purpose because
                ## a) users should clean their meshes themselves, and
                ## b) this will allow some artistic effects
                # if object_eval.matrix_world.determinant() < 0.0:
                #     mesh.flip_normals()

                if not mesh.loop_triangles:
                    object_eval.to_mesh_clear()
                    mesh = None

            # TODO implement new normals handling
            if mesh:
                mesh.split_faces()  # Applies smooth by angle operator

        yield mesh
    finally:
        if object_eval and mesh:
            object_eval.to_mesh_clear()
