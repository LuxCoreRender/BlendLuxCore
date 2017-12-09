import bpy
from bpy.props import EnumProperty, StringProperty


class LuxCoreConfig(bpy.types.PropertyGroup):
    engines = [
        ("PATHCPU", "Path CPU", "Path tracer", 0),
        ("TILEPATHCPU", "Tile Path CPU", "Path tracer rendering in tiles", 1),
        ("BIDIRCPU", "Bidir CPU", "Bidirectional path tracer", 2),
        ("PATHOCL", "Path OpenCL", "OpenCL version of Path CPU", 3),
        ("TILEPATHOCL", "Tile Path OpenCL", "OpenCL version of Tile Path CPU", 4),
    ]
    engine = EnumProperty(name="Engine", items=engines)

    samplers = [
        ("SOBOL", "Sobol", "Recommended for scenes with simple lighting (outdoors, studio setups)", 0),
        ("METROPOLIS", "Metropolis", "Recommended for scenes with difficult lighting (caustics, indoors)", 1),
    ]
    sampler = EnumProperty(name="Sampler", items=samplers)
