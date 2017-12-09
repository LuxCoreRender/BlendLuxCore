import bpy
from bpy.props import PointerProperty, EnumProperty


def init():
    bpy.types.Scene.luxcore = PointerProperty(type=LuxCoreSceneProps)


class LuxCoreSceneProps(bpy.types.PropertyGroup):
    engines = [
        ("PATHCPU", "Path CPU", "Path tracer", 0),
        ("TILEPATHCPU", "Tile Path CPU", "Path tracer rendering in tiles", 1),
        ("BIDIRCPU", "Bidir CPU", "Bidirectional path tracer", 2),
        ("PATHOCL", "Path OpenCL", "OpenCL version of Path CPU", 3),
        ("TILEPATHOCL", "Tile Path OpenCL", "OpenCL version of Tile Path CPU", 4),
    ]
    engine = EnumProperty(name="Engine", items=engines)
