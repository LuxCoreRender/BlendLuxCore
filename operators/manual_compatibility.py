import bpy
import math
from ..nodes import TREE_TYPES
from ..utils.node import find_nodes

# TODO:
#  * The ImagePipeline tonemapper default settings were changed: auto brightness is now disabled by default (was enabled),
#    gain is now 1.0 by default (was 0.5)

# TODO prevent user from pressing the button twice

def calc_power_correction_factor(spread_angle):
    return math.pi * (2 * math.pi * (1 - math.cos(spread_angle / 2)))


class LUXCORE_OT_convert_to_v23(bpy.types.Operator):
    bl_idname = "luxcore.convert_to_v23"
    bl_label = "Convert Scene From v2.2 or Earlier to v2.3"
    bl_description = ""
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        """
        When this operator is run, we can assume that the scene was saved with v2.2 or earlier, and is now open in v2.3.
        (which we can't assume in the utils/compatibility.py script)
        """

        for light in bpy.data.lights:
            if light.type == "SUN":
                if light.luxcore.light_type == "sun":
                    # Sun and sky now have a separate gain property with default 0.00002 to prevent overexposion
                    # with default tonemapper settings. In old scenes, copy the old gain value.
                    light.luxcore.sun_sky_gain = light.luxcore.gain
                    light.update_tag()
                elif light.luxcore.light_type == "distant":
                    # The distant light is now normalized by default. For scenes created in older versions,
                    # disable the normalize option to get the same result
                    light.luxcore.normalize_distant = False
                    light.update_tag()
            
            # Converting Area lights so new Power matches 2.2 power per unit angle
            if light.type == "AREA":
                light.luxcore.light_unit = "power"
                light.luxcore.power *= calc_power_correction_factor(light.luxcore.spread_angle)
                light.update_tag()

        for world in bpy.data.worlds:
            if world.luxcore.light == "sky2":
                # Sun and sky now have a separate gain property with default 0.00002 to prevent overexposion
                # with default tonemapper settings. In old scenes, copy the old gain value.
                world.luxcore.sun_sky_gain = world.luxcore.gain
                world.update_tag()

        for node_tree in bpy.data.node_groups:
            if node_tree.bl_idname not in TREE_TYPES:
                continue

            # The blackbody texture is now normalized by default. For scenes created in older versions, disable
            # the normalize option to get the same result
            for blackbody_node in find_nodes(node_tree, "LuxCoreNodeTexBlackbody", False):
                blackbody_node.normalize = False
            
            # Converting Emissive materials so new Power matches 2.2 power per unit angle
            for emission_node in find_nodes(node_tree, "LuxCoreNodeMatEmission", False):
                emission_node.emission_unit = "power"
                emission_node.power *= calc_power_correction_factor(emission_node.spread_angle)
            

        return {"FINISHED"}