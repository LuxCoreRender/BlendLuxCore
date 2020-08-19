import bpy
from bpy.props import (
    CollectionProperty, PointerProperty, BoolProperty,
    FloatProperty, FloatVectorProperty, StringProperty
)
from bpy.types import PropertyGroup
from ..utils import node as utils_node

import re

# OpenCL engines support 8 lightgroups
MAX_LIGHTGROUPS = 8
# However one group is always there (the default group), so 7 can be user-defined
MAX_CUSTOM_LIGHTGROUPS = MAX_LIGHTGROUPS - 1

RGB_GAIN_DESC = "The color of each light in this group is multiplied with this multiplier, if enabled"
TEMP_DESC = "Blackbody emission color in Kelvin by which to shift the color of each light in this group"


class LuxCoreLightGroup(PropertyGroup):
    def name_set(self, value):
        old_name = self.get("name", "")
        new_name = value
        
        if new_name == old_name:
            return
        
        # Prevent empty name
        if new_name == "":
            new_name = "Can't be empty"
        
        # Prevent name collisions
        groups = bpy.context.scene.luxcore.lightgroups.get_all_groups()
        names = {group.name for group in groups}
        i = 0
        new_name_base = new_name
        while new_name in names:
            i += 1
            new_name = new_name_base + ".%03d" % i
        
        # Apply change
        self["name"] = new_name
        
        # After a rename, update all occurences of the name automatically
        relevant_node_types = {
            "LuxCoreNodeMatEmission",
            "LuxCoreNodeVolClear",
            "LuxCoreNodeVolHomogeneous",
            "LuxCoreNodeVolHeterogeneous",
        }

        for mat in bpy.data.materials:
            node_tree = mat.luxcore.node_tree
            if mat.library or not node_tree:
                continue

            for node in utils_node.find_nodes_multi(node_tree, relevant_node_types, follow_pointers=True):
                if node.lightgroup and node.lightgroup == old_name:
                    node.lightgroup = new_name

        for obj in bpy.data.objects:
            if obj.library:
                continue
            if obj.type == "LIGHT":
                lux_light = obj.data.luxcore
                if lux_light.lightgroup and lux_light.lightgroup == old_name:
                    lux_light.lightgroup = new_name
                
    def name_get(self):
        return self.get("name", "")

    name: StringProperty(name="Name", set=name_set, get=name_get)

    # These settings are no longer used, TODO: remove?
    enabled: BoolProperty(default=True, name="Enabled",
                          description="Enable/disable this light group. If disabled, all lights "
                                      "in this group are off. Does not affect this lightgroup's AOV")
    show_settings: BoolProperty(default=True)
    gain: FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    use_rgb_gain: BoolProperty(name="Color:", default=True, description="Use RGB color multiplier")
    rgb_gain: FloatVectorProperty(name="", default=(1, 1, 1), min=0, max=1, subtype="COLOR",
                                   description=RGB_GAIN_DESC)
    use_temperature: BoolProperty(name="Temperature:", default=False,
                                   description="Use temperature multiplier")
    temperature: FloatProperty(name="Kelvin", default=4000, min=1000, max=10000, precision=0,
                                description=TEMP_DESC)


# Attached to scene
class LuxCoreLightGroupSettings(PropertyGroup):
    default: PointerProperty(type=LuxCoreLightGroup)
    custom: CollectionProperty(type=LuxCoreLightGroup)

    def add(self):
        if len(self.custom) < MAX_CUSTOM_LIGHTGROUPS:
            new_group = self.custom.add()
            # +1 because the default group is 0
            new_group.name = "Light Group %d" % (len(self.custom) + 1)
            return new_group

    def remove(self, index):
        self.custom.remove(index)

    def get_id_by_name(self, group_name):
        # Check if the name is in the custom groups
        for i, group in enumerate(self.custom):
            if group.name == group_name:
                # Add 1 because 0 is the default group
                return i + 1
        # Fallback to default group
        return 0

    def get_group_by_name(self, group_name):
        for group in self.custom:
            if group.name == group_name:
                return group
        return self.default

    @staticmethod
    def get_lightgroup_pass_name(group_name="", group_index=-1, is_default_group=False):
        """
        Get the name used for a lightgroup in the Blender render passes of a render layer.
        This name is used both as a key and in the UI, so it uses a nice formatting
        and the numbering starts from 1 instead of 0.
        """
        if is_default_group:
            return 'LG %d: "%s"' % (1, "Default Lightgroup")
        else:
            # +1 because the default group is 0
            # another +1 to get natural numbering starting at 1 instead of 0
            return 'LG %d: "%s"' % (group_index + 2, group_name)

    def get_pass_names(self):
        """
        Get a list of formatted names of all lightgroups in the scene.
        These names are used both as keys and in the UI, so they use a nice formatting
        and the numbering starts from 1 instead of 0.
        """
        names = [self.get_lightgroup_pass_name(is_default_group=True)]

        for i, group in enumerate(self.custom):
            names.append(self.get_lightgroup_pass_name(group.name, i))

        return names

    def get_all_groups(self):
        return [self.default] + [group for group in self.custom]


def is_lightgroup_pass_name(string):
    return re.fullmatch(r"LG \d: \".*\"", string)
