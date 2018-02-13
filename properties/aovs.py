import bpy
from bpy.props import PointerProperty, BoolProperty
from bpy.types import PropertyGroup


# Note: currently attached to scene because we don't support render layers
class LuxCoreAOVSettings(PropertyGroup):
    # TODO: descriptions
    # Basic Information
    rgb = BoolProperty(name="RGB", default=False)
    rgba = BoolProperty(name="RGBA", default=False)
    alpha = BoolProperty(name="Alpha", default=False)
    depth = BoolProperty(name="Depth", default=True)

    # Material/Object Information
    material_id = BoolProperty(name="Material ID", default=False)
    object_id = BoolProperty(name="Object ID", default=False)
    emission = BoolProperty(name="Emission", default=False)

    # Direct Light Information
    direct_diffuse = BoolProperty(name="Direct Diffuse", default=False)
    direct_glossy = BoolProperty(name="Direct Glossy", default=False)

    # Indirect Light Information
    indirect_diffuse = BoolProperty(name="Indirect Diffuse", default=False)
    indirect_glossy = BoolProperty(name="Indirect Glossy", default=False)
    indirect_specular = BoolProperty(name="Indirect Specular", default=False)

    # Geometry Information
    position = BoolProperty(name="Position", default=False)
    shading_normal = BoolProperty(name="Shading Normal", default=False)
    geometry_normal = BoolProperty(name="Geometry Normal", default=False)
    uv = BoolProperty(name="UV", default=False)

    # Shadow Information
    direct_shadow_mask = BoolProperty(name="Direct Shadow Mask", default=False)
    indirect_shadow_mask = BoolProperty(name="Indirect Shadow Mask", default=False)

    # Render Information
    raycount = BoolProperty(name="Raycount", default=False)
    samplecount = BoolProperty(name="Samplecount", default=False)
    convergence = BoolProperty(name="Convergence", default=False)
    irradiance = BoolProperty(name="Irradiance", default=False)
