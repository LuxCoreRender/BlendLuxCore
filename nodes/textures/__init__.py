import nodeitems_utils
from .tree import luxcore_node_categories_texture

# Import all texture nodes just so they get registered
# TODO 2.8 remove
from .band import LuxCoreNodeTexBand
from .blackbody import LuxCoreNodeTexBlackbody
from .blenderblend import LuxCoreNodeTexBlenderBlend
from .blenderclouds import LuxCoreNodeTexBlenderClouds
from .blenderdistortednoise import LuxCoreNodeTexBlenderDistortedNoise
from .blendermagic import LuxCoreNodeTexBlenderMagic
from .blendermarble import LuxCoreNodeTexBlenderMarble
from .blendermusgrave import LuxCoreNodeTexBlenderMusgrave
from .blendernoise import LuxCoreNodeTexBlenderNoise
from .blenderstucci import LuxCoreNodeTexBlenderStucci
from .blendervoronoi import LuxCoreNodeTexBlenderVoronoi
from .blenderwood import LuxCoreNodeTexBlenderWood
from .brick import LuxCoreNodeTexBrick
from .bump import LuxCoreNodeTexBump
from .checkerboard2d import LuxCoreNodeTexCheckerboard2D
from .checkerboard3d import LuxCoreNodeTexCheckerboard3D
from .coloratdepth import LuxCoreNodeTexColorAtDepth
from .colormix import LuxCoreNodeTexColorMix
from .constfloat1 import LuxCoreNodeTexConstfloat1
from .constfloat3 import LuxCoreNodeTexConstfloat3
from .dots import LuxCoreNodeTexDots
from .dotproduct import LuxCoreNodeTexDotProduct
from .fbm import LuxCoreNodeTexfBM
from .fresnel import LuxCoreNodeTexFresnel
from .hitpoint import LuxCoreNodeTexHitpoint
from .hsv import LuxCoreNodeTexHSV
from .imagemap import LuxCoreNodeTexImagemap
from .invert import LuxCoreNodeTexInvert
from .iorpreset import LuxCoreNodeTexIORPreset
from .irregulardata import LuxCoreNodeTexIrregularData
from .lampspectrum import LuxCoreNodeTexLampSpectrum
from .makefloat3 import LuxCoreNodeTexMakeFloat3
from .mapping2d import LuxCoreNodeTexMapping2D
from .mapping3d import LuxCoreNodeTexMapping3D
from .marble import LuxCoreNodeTexMarble
from .math import LuxCoreNodeTexMath
from .normalmap import LuxCoreNodeTexNormalmap
from .objectid import LuxCoreNodeTexObjectID
from .output import LuxCoreNodeTexOutput
from .pointiness import LuxCoreNodeTexPointiness
from .remap import LuxCoreNodeTexRemap
from .hitpointinfo import LuxCoreNodeTexHitpointInfo
from .smoke import LuxCoreNodeTexSmoke
from .splitfloat3 import LuxCoreNodeTexSplitFloat3
from .uv import LuxCoreNodeTexUV
from .vectormath import LuxCoreNodeTexVectorMath
from .wrinkled import LuxCoreNodeTexWrinkled
from .windy import LuxCoreNodeTexWindy


def register():
    nodeitems_utils.register_node_categories("LUXCORE_TEXTURE_TREE", luxcore_node_categories_texture)


def unregister():
    nodeitems_utils.unregister_node_categories("LUXCORE_TEXTURE_TREE")
