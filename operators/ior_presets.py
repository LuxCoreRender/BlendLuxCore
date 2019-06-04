""" BlendLuxCore operator and data classes to support the LuxCoreNodeIORPreset
    class in module BlendLuxCore/nodes/textures/iorpreset"""
# <pep8 compliant>
import copy
import bpy
from bpy.props import EnumProperty, StringProperty, IntProperty

# Refractive Index value references:
#   https://refractiveindex.info/
#   https://en.wikipedia.org/wiki/List_of_refractive_indices
#   https://en.wikipedia.org/wiki/Calcite


class LuxCoreIORPresetValues():
    """Class to contain IOR preset items, and return them in
       a list of tuples suitable for an EnumProperty"""

    # ior_values format: 'ior_values["unique_id"] = ["name", value]'
    # The ior_values items can be listed here in any order, as they will
    # be sorted when they are converted to a list as required by EnumProperty.
    _ior_values = {
        "acetone": ["Acetone", 1.36],
        "acrylic_glass": ["Acrylic Glass", 1.49],
        "air_0C": ["Air @ 0C", 1.000293],
        "air_stp": ["Air @ STP", 1.000277],
        "amber": ["Amber", 1.55],
        "blood": ["Blood", 1.301],
        "calcite_e": ["Calcite (extraordinary)", 1.486],
        "calcite_o": ["Calcite (ordinary)", 1.658],
        "cellulose": ["Cellulose", 1.47],
        "crown_glass_pure": ["Crown glass (pure)", 1.52],
        "cubic_zirconia": ["Cubic zirconia", 2.15],
        "diamond": ["Diamond", 2.415],
        "ethanol_20C": ["Ethanol @ 20C", 1.36],
        "flint_glass_dense": ["Flint glass (dense)", 1.71],
        "flint_glass_pure": ["Flint glass (pure)", 1.61],
        "glycerine": ["Glycerine", 1.47],
        "nacl": ["Sodium Chloride", 1.544],
        "olive_oil": ["Olive Oil", 1.46],
        "opal": ["Opal", 1.44],
        "pet_plastic": ["PET plastic", 1.5750],
        "plate_glass": ["Plate Glass", 1.52],
        "polycarbonate": ["Polycarbonate", 1.584],
        "polystyrene": ["Polystyrene", 1.52],
        "pyrex_glass": ["Pyrex Glass", 1.470],
        "quartz": ["Quartz", 1.458],
        "sapphire": ["Sapphire", 1.77],
        "silicone_oil_20C": ["Silicone Oil @ 20C", 1.4],
        "turpentine": ["Turpentine", 1.47],
        "vacuum": ["Vacuum", 1],
        "water_20C": ["Water @ 20C", 1.330],
        "water_ice": ["Water Ice", 1.31]
    }

    # A default value that will be assigned an integer index of 0 as required
    # by EnumProperty when using a callback to obtain the list of items.
    default_key = "water_20C"

    @classmethod
    def get_sorted_list(cls, sort="name"):
        # Make a deep copy of the ior_values dict
        ior_values = copy.deepcopy(cls._ior_values)
        # Append a unique integer index to each tuple. The EnumProperty needs
        # this to determine a default item (index 0) when using a callback.
        # Failure to do so results in a random item becoming the default.
        ior_values[cls.default_key].append(0)
        index = 1
        for ior in ior_values:
            if ior != cls.default_key:
                ior_values[ior].append(index)
                index += 1
        # Convert the dict to a sorted list of tuples
        if sort == "value":
            index = 1
        else:
            index = 0
        preset_list = []
        for item in sorted(ior_values.items(),
                           key=lambda e: e[1][index]):
            text = "{} ({:f})".format(item[1][0], item[1][1])
            preset_list.append((item[0], text, text, item[1][2]))
        return preset_list

    @classmethod
    def get_item(cls, key=default_key):
        return cls._ior_values[key]

    @classmethod
    def get_value(cls, key=default_key):
        return cls._ior_values[key][1]


# It seems that Blender *Property classes do not support inheritance if
# there are methods in the same class. The following classes
# (LuxCoreIORPresetCommonProperties, LuxCoreIORPresetBase,
#  LUXCORE_OT_ior_preset_names  and LUXCORE_OT_ior_preset_values) are an
# attempt at minimizing code duplication within the limits imposed by Blender.
class LuxCoreIORPresetCommonProperties():
    """ A property-only class to work around Blender's inheritance limits. """
    bl_idname = "luxcore.ior_preset_common_properties"
    bl_label = ""
    node_name: StringProperty()
    node_tree_index: IntProperty()


class LuxCoreIORPresetBase(LuxCoreIORPresetCommonProperties):
    """ A base class for LUXCORE_OT_ior_preset_* common methods. Do not call"""

    bl_idname = "luxcore.ior_preset_base"

    def cb_ior_preset(self, context):
        return []

    ior_preset: EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)

    def execute(self, context):
        ior_name, ior_value = LuxCoreIORPresetValues.get_item(self.ior_preset)
        node = bpy.data.node_groups[self.node_tree_index].nodes[self.node_name]
        node.ior_name_text = ior_name
        node.ior_value_text = str(ior_value)
        node.ior_value_float = ior_value
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class LUXCORE_OT_ior_preset_names(bpy.types.Operator,
                                  LuxCoreIORPresetBase,
                                  LuxCoreIORPresetCommonProperties):
    """ A custom operator to return a list of IOR presets sorted by name """

    bl_idname = "luxcore.ior_preset_names"
    bl_description = "Index of Refraction presets sorted by name"
    bl_property = "ior_preset"

    callback_strings = []

    def cb_ior_preset(self, context):
        items = LuxCoreIORPresetValues.get_sorted_list("name")
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LUXCORE_OT_ior_preset_names.callback_strings = items
        return items

    ior_preset: EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)


class LUXCORE_OT_ior_preset_values(bpy.types.Operator,
                                   LuxCoreIORPresetBase,
                                   LuxCoreIORPresetCommonProperties):
    """ A custom operator to return a list of IOR presets sorted by value """

    bl_idname = "luxcore.ior_preset_values"
    bl_description = "Index of Refraction presets sorted by value"
    bl_property = "ior_preset"

    callback_strings = []

    def cb_ior_preset(self, context):
        items = LuxCoreIORPresetValues.get_sorted_list("value")
        # There is a known bug with using a callback,
        # Python must keep a reference to the strings
        # returned or Blender will misbehave or even crash.
        LUXCORE_OT_ior_preset_values.callback_strings = items
        return items

    ior_preset: EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)
