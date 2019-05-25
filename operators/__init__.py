from platform import system
from os import environ

# Fix problem of OpenMP calling a trap about two libraries loading because blender's
# openmp lib uses @loader_path and zip does not preserve symbolic links (so can't
# spoof loader_path with symlinks)
if system() == "Darwin":
    environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure initialization (note: no need to initialize utils)
# TODO 2.8 remove
from . import (
    camera, camera_response_func, debug, general, ior_presets, lightgroups,
    material, multi_image_import, node_tree_presets, pointer_node,
    pyluxcoretools, texture, update, world,
)
