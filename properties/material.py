import bpy
from bpy.props import PointerProperty


def init():
    bpy.types.Material.luxcore = PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialProps(bpy.types.PropertyGroup):
    # TODO: waiting for a fix: https://developer.blender.org/T53509
    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
    interior_volume = PointerProperty(name="Interior Volume", type=bpy.types.NodeTree)
    exterior_volume = PointerProperty(name="Exterior Volume", type=bpy.types.NodeTree)
