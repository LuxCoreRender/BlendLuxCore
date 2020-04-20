from platform import system
from os import environ

# Fix problem of OpenMP calling a trap about two libraries loading because blender's
# openmp lib uses @loader_path and zip does not preserve symbolic links (so can't
# spoof loader_path with symlinks)
if system() == "Darwin":
    environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
