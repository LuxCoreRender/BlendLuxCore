import bpy
from bpy.props import (
    PointerProperty, BoolProperty, FloatProperty, IntProperty,
    EnumProperty, StringProperty, FloatVectorProperty,
)
from bpy.types import PropertyGroup
from .image_user import LuxCoreImageUser
from .light import GAMMA_DESCRIPTION


#def init():
#    bpy.types.ParticleSettings.luxcore = PointerProperty(type=LuxCoreParticlesProps)


TESSEL_ITEMS = [
    ("ribbon", "Triangle Ribbon", "Render hair as ribbons of triangles facing the camera"),
    ("ribbonadaptive", "Adaptive Triangle Ribbon", "Render hair as ribbons of triangles facing the camera, "
                                                   "using more triangles for hair close to the camera"),
    ("solid", "Solid", "Render hairs as solid mesh cylinders (memory intensive!)"),
    ("solidadaptive", "Adaptive Solid", "Render hairs as solid mesh cylinders, "
                                        "using more subdivisions for hair close to the camera"),
]

COLOREXPORT_ITEMS = [
    ("vertex_color", "From Emitter Vertex Colors", "Copy emitter vertex colors to hair vertex colors. "
                                                   "This option increases the memory usage of the hair"),
    ("uv_texture_map", "From UV Texture Map", "Copy colors from an image texture to hair vertex colors. "
                                              "This option increases the memory usage of the hair"),
    ("none", "White", "Do not set the hair vertex colors (they will be white). This option does not "
                      "increase the memory usage of the hair (if both color multipliers are left at white)"),
]

INSTANCING_TYPES = [
    ("enabled", "Save Memory", "Instance the hair mesh to save memory "
                               "(reduces rendering performance of the hair)", 0),
    ("disabled", "Improve Performance", "Do not instance the mesh, this increasees the rendering "
                                        "performance of the hair, but costs more memory", 1),
]

COPY_UV_COORDS_DESC = (
    "Create UV coordinates for the hair, using a UV mapping of the emitter mesh. "
    "This option will allow you to control the hair color with any UV mapped texture, just like a normal mesh"
)

VERTEX_COL_MULTIPLIERS_DESC = (
    "Vertex color multiplier. If root and tip colors are white (1, 1, 1), they will not be used. "
    "Otherwise, they will be interpolated over each hair strand and multiplied with the vertex colors "
    "from the emitter or texture map, if used"
)


class LuxCoreHair(PropertyGroup):
    """
    LuxCore Hair Rendering settings
    """
    
    hair_size: FloatProperty(name="Hair Thickness", default=0.001, min=0.000001,
                              max=1000.0, precision=3, step=0.0001, subtype="DISTANCE",
                              unit="LENGTH", description="Diameter of the individual hair strands")

    root_width: FloatProperty(name="Root", default=100, min=0.0001, max=100,
                               precision=0, subtype="PERCENTAGE",
                               description="Thickness of hair at root")
    
    tip_width: FloatProperty(name="Tip", default=100, min=0.0001, max=100,
                              precision=0, subtype="PERCENTAGE",
                              description="Thickness of hair at root")
    
    width_offset: FloatProperty(name="Offset", default=0, min=0.0001, max=100,
                                 precision=0, subtype="PERCENTAGE",
                                 description="Offset from root for thickness variation")
    
    tesseltype: EnumProperty(name="Tessellation Type", default="ribbonadaptive", items=TESSEL_ITEMS,
                              description="Tessellation method for hair strands")
    
    adaptive_maxdepth: IntProperty(name="Max Depth",
                                    default=8, min=1, soft_min=2, soft_max=12, max=24,
                                    description="Maximum tessellation depth for adaptive modes")
    
    solid_sidecount: IntProperty(name="Number of Sides", default=3, min=3, soft_max=8, max=64,
                                  description="Number of sides for each hair cylinder")    
    
    solid_capbottom: BoolProperty(name="Cap Root", default=False,
                                   description="Add a base cap to each hair cylinder")
    
    solid_captop: BoolProperty(name="Cap Top", default=False,
                                description="Add an end cap to each hair cylinder")
    
    adaptive_error: FloatProperty(name="Max Error", default=0.1, min=0.001, max=0.9,
                                   description="Maximum tessellation error for adaptive modes")
    
    export_color: EnumProperty(name="Vertex Colors", default="none", items=COLOREXPORT_ITEMS,
                                description="Choose which attributes of the emitter mesh "
                                            "should be copied to the hair vertex colors.\n"
                                            "You can access them with the Vertex Color texture in the hair material")

    use_active_uv_map: BoolProperty(name="Use Active UV Map", default=True)
    # Only shown if use_active_uv_map is False.
    # Note: unfortunately we can't use a PointerProperty here because
    # bpy.types.MeshUVLoopLayer inherits from bpy_struct instead of bpy.types.ID
    uv_map_name: StringProperty(name="UV Map", default="",
                                 description="UV Map to use. If empty, the active UV Map is used")
    image: PointerProperty(name="Image", type=bpy.types.Image)
    image_user: PointerProperty(type=LuxCoreImageUser)
    gamma: FloatProperty(name="Gamma", default=2.2, min=0, description=GAMMA_DESCRIPTION)

    use_active_vertex_color_layer: BoolProperty(name="Use Active Vertex Color Layer", default=True)
    vertex_color_layer_name: StringProperty(name="Vertex Color Layer", default="",
                                             description="Vertex color layer to use. If empty, the active one is used")

    copy_uv_coords: BoolProperty(name="Copy UV Coordinates", default=True,
                                  description=COPY_UV_COORDS_DESC)

    root_color: FloatVectorProperty(name="Root", default=(1, 1, 1), min=0, max=1, subtype="COLOR",
                                     description=VERTEX_COL_MULTIPLIERS_DESC)
    tip_color: FloatVectorProperty(name="Tip", default=(1, 1, 1), min=0, max=1, subtype="COLOR",
                                    description=VERTEX_COL_MULTIPLIERS_DESC)

    instancing: EnumProperty(name="Optimization", default="disabled", items=INSTANCING_TYPES,
                              description="Note: Only affects CPU rendering")


class LuxCoreParticlesProps(PropertyGroup):
    hair: PointerProperty(type=LuxCoreHair)

    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.luxcore = PointerProperty(
            name="LuxCore Particle Settings",
            description="LuxCore particle settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.ParticleSettings.luxcore

