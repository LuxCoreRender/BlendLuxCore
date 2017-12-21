import bpy
from bpy.props import PointerProperty


def init():
    bpy.types.Material.luxcore = PointerProperty(type=LuxCoreMaterialProps)

    # Also attach to object as fallback for now because of Blender bug.
    # This only allows to have one material per object.
    # TODO: waiting for a fix: https://developer.blender.org/T53509
    bpy.types.Object.luxcore = PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialProps(bpy.types.PropertyGroup):
    # TODO: waiting for a fix: https://developer.blender.org/T53509
    node_tree = PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
