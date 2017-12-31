from .checkerboard3d import LuxCoreNodeTexCheckerboard3D
from .imagemap import LuxCoreNodeTexImagemap
from .fresnel import LuxCoreNodeTexFresnel
from .mapping2d import LuxCoreNodeTexMapping2D
from .mapping3d import LuxCoreNodeTexMapping3D

# TODO I want optional separate texture node trees so the user can re-use
# complex texture setups in multiple materials/volumes

# TODO: how to warn if some texture nodes are incompatible with materials/volumes
# they are used in?
