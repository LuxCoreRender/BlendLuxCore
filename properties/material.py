import bpy
from bpy.props import PointerProperty


def init():
    bpy.types.Material.luxcore = PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialProps(bpy.types.PropertyGroup):
    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
