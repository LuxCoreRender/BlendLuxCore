RGB_GAIN_DESC = (
    "The color of this light.\n"
    "Note that some lights have an inherent color, e.g. sun, sky, HDRI or textured lights.\n"
    "For those lights, their inherent color is multiplied with this color"
)

IMPORTANCE_DESCRIPTION = (
    "A hint how much processing power to spend on this "
    "light compared to other lights"
)

POWER_DESCRIPTION = (
    "Power in watt; setting 0 for both power and efficacy bypasses "
    "this feature and uses only the light gain"
)

NORMALIZEBYCOLOR_DESCRIPTION = (
    "Normalize intensity by the Color Luminance.\n"
    "Recommended for Photometric units (Lumen, Candela, Lux) to simulate \n"
    "the luminous efficiency function"
)

EXPOSURE_DESCRIPTION = (
    "Power-of-2 step multiplier. "
    "An EV step of 1 will double the brightness of the light"
)

EFFICACY_DESCRIPTION = (
    "Luminous efficacy in lumens per watt"
)

LUMEN_DESCRIPTION = (
    "Luminous flux in lumens, assuming a maximum possible luminous efficacy of 683 lm/W.\n"
    "Photometric unit, it should be normalized by Color Luminance.\n"
    "Best for Point lights, using Lightbulb packages as reference"
)

CANDELA_DESCRIPTION = (
    "Luminous intensity in candela (luminous power per unit solid angle).\n"
    "Photometric unit, it should be normalized by Color Luminance.\n"
    "Best for Spot lights to maintain brighness when changing Angle"
)

PER_SQUARE_METER_DESCRIPTION = (
    "Divides intensity by the object surface to maintain brightness when changing Size.\n"
    "Candela per square meter is also called Nit"
)

LUX_DESCRIPTION = (
    "Illuminance in Lux (luminous flux incident on a surface in lumen per square meter).\n"
    "Photometric unit, it should be normalized by Color Luminance"
)

GAMMA_DESCRIPTION = (
    "Gamma value of the image. Most HDR/EXR images use 1.0, while "
    "most JPG/PNG images use 2.2"
)

SAMPLEUPPERHEMISPHEREONLY_DESCRIPTION = (
    "Used to avoid shadows cast from below when using shadow catcher"
)

SPREAD_ANGLE_DESCRIPTION = (
    "How directional the light is emitted, set as the half-angle of the light source. "
    "Default is 90°. Smaller values mean that more light is emitted in the direction "
    "of the light and less to the sides"
)

LIGHTGROUP_DESC = "Add this light to a light group from the scene"

TURBIDITY_DESC = (
    "Amount of dust/fog/particles/smog in the air "
    "(will only affect the sun/sky color, but not add volumetric fog)"
)

VIS_INDIRECT_BASE = (
    "Visibility for indirect {type} rays. "
    "If disabled, this light will appear black in indirect bounces on {type} materials"
)
VIS_INDIRECT_DIFFUSE_DESC = VIS_INDIRECT_BASE.format(type="diffuse") + " (e.g. matte)"
VIS_INDIRECT_GLOSSY_DESC = VIS_INDIRECT_BASE.format(type="glossy") + " (e.g. glossy, roughglass, metal)"
VIS_INDIRECT_SPECULAR_DESC = VIS_INDIRECT_BASE.format(type="specular") + " (e.g. glass, mirror)"

RELSIZE_DESC = "1.0 is the apparent size of the sun when observed from earth (at mean distance of 149,600,000 km)"
THETA_DESC = "Half angle in degrees. Larger values make the light source appear larger and the shadows softer"
NORMALIZE_DISTANT_DESC = "Make the brightness received at surfaces independent from the size of this light"
SUN_SKY_GAIN_DESC = (
    "Brightness multiplier. Set to 1 for physically correct sun/sky brightness, "
    "if you also use physically based tonemapper and light settings"
)
