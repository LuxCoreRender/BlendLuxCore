import bpy
import math
from ..nodes import TREE_TYPES
from ..utils.node import find_nodes


def calc_power_correction_factor(spread_angle):
    return (2 * math.pi * (1 - math.cos(spread_angle / 2)))


class LUXCORE_OT_convert_to_v23(bpy.types.Operator):
    bl_idname = "luxcore.convert_to_v23"
    bl_label = "Convert Scene From v2.2 or Earlier to v2.3"
    bl_description = ("Convert various settings (e.g. light brightness, world settings) so scenes "
                      "created with LuxCore v2.2 or earlier appear the same when rendered in v2.3")
    bl_options = {"UNDO"}

    was_executed = False

    @classmethod
    def poll(cls, context):
        return not cls.was_executed

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
                elif light.luxcore.light_type == "distant":
                    # The distant light is now normalized by default. For scenes created in older versions,
                    # disable the normalize option to get the same result
                    light.luxcore.normalize_distant = False
            else:
                # LuxCore behaviour is to use only the gain if power or efficacy are 0, so in this case
                # it is ok to leave the new default "artistic" which uses only gain
                if light.luxcore.power != 0 and light.luxcore.efficacy != 0:
                    light.luxcore.light_unit = "power"
                    light.luxcore.power *= light.luxcore.gain

                    if light.type == "AREA" and not light.luxcore.is_laser:
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

            # Note: for some reason we don't have to disable the new normalize option.

            for emission_node in find_nodes(node_tree, "LuxCoreNodeMatEmission", False):
                # LuxCore behaviour is to use only the gain if power or efficacy are 0, so in this case
                # it is ok to leave the new default "artistic" which uses only gain
                if emission_node.power != 0 and emission_node.efficacy != 0:
                    emission_node.emission_unit = "power"
                    emission_node.power *= emission_node.gain * calc_power_correction_factor(emission_node.spread_angle)

        if context.scene.camera:
            tonemapper = context.scene.camera.data.luxcore.imagepipeline.tonemapper
            # When the tonemapper settings are set to our new defaults, this could mean two things:
            # a) The user has chosen these settings in v2.2 on his own. In this case they shouldn't be changed.
            # b) The user has never touched these settings and they were automatically changed to the new defaults
            #    by Blender. In this case, we should change them back to the old defaults.
            #
            # Unfortunately, there is no way to find out which of these options is the case.
            # So we just print a warning and leave the settings as they are.
            using_new_defaults = tonemapper.linear_scale == 1 and not tonemapper.use_autolinear
            if tonemapper.type == "TONEMAP_LINEAR" and using_new_defaults:
                # Not really an error, but if I use INFO or WARNING, Blender doesn't show a popup
                self.report({"ERROR"}, "Could not auto-convert the tonemapper settings. If this scene "
                                       "was using the old default settings (Auto enabled, gain 0.5), you "
                                       "will have to restore them manually")

        LUXCORE_OT_convert_to_v23.was_executed = True
        return {"FINISHED"}
