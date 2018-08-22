import bpy
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup
from ..operators.blender_mesh import LUXCORE_OT_use_proxy_switch

DESC_USE_PROXY = "Use the mesh as a proxy for quick viewport response"
DESC_PROXIES = "Filepath to the high res meshes used in rendering"
DESC_FILEPATH = "Path to a .ply file which is loaded at render time and replaces the low-poly proxy mesh"


def init():
    bpy.types.Mesh.luxcore = PointerProperty(type=LuxCoreMeshProps)
    bpy.types.Curve.luxcore = PointerProperty(type=LuxCoreMeshProps)
    bpy.types.MetaBall.luxcore = PointerProperty(type=LuxCoreMeshProps)


class LuxCoreProxyList(PropertyGroup):
    name = StringProperty()
    matIndex = IntProperty()
    filepath = StringProperty(subtype='FILE_PATH', description=DESC_FILEPATH)


class LuxCoreMeshProps(PropertyGroup):
    use_proxy = BoolProperty(name="Use as Proxy", default=False, update=LUXCORE_OT_use_proxy_switch, description=DESC_USE_PROXY)
    proxies = CollectionProperty(name="Proxy Files", type=LuxCoreProxyList, description=DESC_PROXIES)    
