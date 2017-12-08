import bpy


def init():
    bpy.types.Material.luxcore = bpy.props.PointerProperty(type=LuxCoreMaterialProps)


class LuxCoreMaterialProps(bpy.types.PropertyGroup):
    # TODO: waiting for a fix: https://developer.blender.org/T53509
    node_tree = bpy.props.PointerProperty(name="Node Tree", type=bpy.types.NodeTree)
