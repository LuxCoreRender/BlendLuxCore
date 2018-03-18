import bpy
from bpy.props import PointerProperty, BoolProperty
from bpy.types import PropertyGroup


# Attached to render layer
class LuxCoreAOVSettings(PropertyGroup):
    def toggle_depth(self, context):
        # Enable/disable Blender's Z pass along with our DEPTH AOV
        # because we use the Blender-defined Z pass instead of a custom one
        # (it is better integrated in the image editor)
        context.scene.render.layers.active.use_pass_z = self.depth

    # Basic Information
    rgb = BoolProperty(name="RGB", default=False,
                       description="Raw RGB values (HDR)")
    rgba = BoolProperty(name="RGBA", default=False,
                       description="Raw RGBA values (HDR)")
    alpha = BoolProperty(name="Alpha", default=False,
                       description="Alpha value [0..1]")
    depth = BoolProperty(name="Depth", default=False,
                         description="Distance from camera (Z-Pass)",
                         update=toggle_depth)

    # Material/Object Information
    material_id = BoolProperty(name="Material ID", default=False,
                       description="Material ID (1 color per material)")
    object_id = BoolProperty(name="Object ID", default=False,
                       description="Object ID (1 color per object)")
    emission = BoolProperty(name="Emission", default=False,
                       description="Emission R, G, B")

    # Direct Light Information
    direct_diffuse = BoolProperty(name="Direct Diffuse", default=False,
                       description="Diffuse R, G, B")
    direct_glossy = BoolProperty(name="Direct Glossy", default=False,
                       description="Glossy R, G, B")

    # Indirect Light Information
    indirect_diffuse = BoolProperty(name="Indirect Diffuse", default=False,
                       description="Indirect diffuse R, G, B")
    indirect_glossy = BoolProperty(name="Indirect Glossy", default=False,
                       description="Indirect glossy R, G, B (e.g. glossy, metal")
    indirect_specular = BoolProperty(name="Indirect Specular", default=False,
                       description="Indirect specular R, G, B (e.g. glass, mirror)")

    # Geometry Information
    position = BoolProperty(name="Position", default=False,
                       description="World X, Y, Z")
    shading_normal = BoolProperty(name="Shading Normal", default=False,
                       description="Normal vector X, Y, Z with mesh smoothing")
    geometry_normal = BoolProperty(name="Geometry Normal", default=False,
                       description="Normal vector X, Y, Z without mesh smoothing")
    uv = BoolProperty(name="UV", default=False,
                       description="Texture coordinates U, V")

    # Shadow Information
    direct_shadow_mask = BoolProperty(name="Direct Shadow Mask", default=False,
                       description="Mask containing shadows by direct light")
    indirect_shadow_mask = BoolProperty(name="Indirect Shadow Mask", default=False,
                       description="Mask containing shadows by indirect light")

    # Render Information
    raycount = BoolProperty(name="Raycount", default=False,
                       description="Ray count per pixel")
    samplecount = BoolProperty(name="Samplecount", default=False,
                       description="Samples per pixel")
    convergence = BoolProperty(name="Convergence", default=False,
                       description="")  # TODO description
    irradiance = BoolProperty(name="Irradiance", default=False,
                       description="Surface irradiance")
