import bpy
from bpy.props import PointerProperty, BoolProperty, FloatProperty, IntProperty, EnumProperty
from bpy.types import PropertyGroup


def init():
    bpy.types.ParticleSettings.luxcore = PointerProperty(type=LuxCoreParticlesProps)


TESSEL_ITEMS = [
    ("ribbon", "Triangle Ribbon", "Render hair as ribbons of triangles facing the camera"),
    ("ribbonadaptive", "Adaptive Triangle Ribbon", "Render hair as ribbons of triangles facing the camera, with adaptive tessellation"),
    ("solid", "Solid", "Render hairs as solid mesh cylinders (memory intensive!)"),
    ("solidadaptive", "Adaptive Solid", "Render hairs as solid mesh cylinders with adaptive tessellation"),
]

COLOREXPORT_ITEMS = [
    ("vertex_color", "Vertex Color", "Use vertex color as hair color"),
    ("uv_texture_map", "UV Texture Map", "Use UV texture map as hair color"),
    ("none", "None", "none"),
]

class LuxCoreHair(PropertyGroup):
    """
    LuxCore Hair Rendering settings
    """
    
    hair_size = FloatProperty(name="Hair Thickness", default=0.001, min=0.000001,
                              max=1000.0, precision=3, step=0.0001, subtype="DISTANCE",
                              unit="LENGTH", description="Diameter of the individual hair strands")

    root_width = FloatProperty(name="Root", default=100, min=0.0001, max=100,
                               precision=0, subtype="PERCENTAGE",
                               description="Thickness of hair at root")
    
    tip_width = FloatProperty(name="Tip", default=100, min=0.0001, max=100,
                              precision=0, subtype="PERCENTAGE",
                              description="Thickness of hair at root")
    
    width_offset = FloatProperty(name="Offset", default=0, min=0.0001, max=100,
                                 precision=0, subtype="PERCENTAGE",
                                 description="Offset from root for thickness variation")
    
    tesseltype = EnumProperty(name="Tessellation Type", default="ribbonadaptive", items=TESSEL_ITEMS, 
                              description="Tessellation method for hair strands")
    
    adaptive_maxdepth = IntProperty(name="Max Tessellation Depth",
                                    default=8, min=1, soft_min=2, soft_max=12, max=24,
                                    description="Maximum tessellation depth for adaptive modes")
    
    solid_sidecount = IntProperty(name="Number of Sides", default=3, min=3, soft_max=8, max=64,
                                  description="Number of sides for each hair cylinder")    
    
    solid_capbottom = BoolProperty(name="Cap Root", default=False,
                                   description="Add a base cap to each hair cylinder")
    
    solid_captop = BoolProperty(name="Cap Top", default=False,
                                description="Add an end cap to each hair cylinder")
    
    adaptive_error = FloatProperty(name="Max Tessellation Error", default=0.1, min=0.001, max=0.9, 
                                   description="Maximum tessellation error for adaptive modes")
    
    export_color = EnumProperty(name="Color Export Mode", default="none", items=COLOREXPORT_ITEMS, 
                                description="Mode of color export for the hair file")

class LuxCoreParticlesProps(PropertyGroup):
    # TODO descriptions
    hair = PointerProperty(type=LuxCoreHair)
