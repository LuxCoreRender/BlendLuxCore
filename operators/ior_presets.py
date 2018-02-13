""" BlendLuxCore operator and data classes to support the LuxCoreNodeIORPreset
    class in module BlendLuxCore/nodes/textures/iorpreset"""
# <pep8 compliant>
import copy
import bpy
from bpy.props import EnumProperty, StringProperty

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
    _ior_values = {}
    _ior_values["acetone"] = ["Acetone", 1.36]
    _ior_values["acrylic_glass"] = ["Acrylic Glass", 1.49]
    _ior_values["air_0C"] = ["Air @ 0C", 1.000293]
    _ior_values["air_stp"] = ["Air @ STP", 1.000277]
    _ior_values["amber"] = ["Amber", 1.55]
    _ior_values["blood"] = ["Blood", 1.301]
    _ior_values["calcite_e"] = ["Calcite (extraordinary)", 1.486]
    _ior_values["calcite_o"] = ["Calcite (ordinary)", 1.658]
    _ior_values["cellulose"] = ["Cellulose", 1.47]
    _ior_values["crown_glass_pure"] = ["Crown glass (pure)", 1.52]
    _ior_values["cubic_zirconia"] = ["Cubic zirconia", 2.15]
    _ior_values["diamond"] = ["Diamond", 2.415]
    _ior_values["ethanol_20C"] = ["Ethanol @ 20C", 1.36]
    _ior_values["flint_glass_dense"] = ["Flint glass (dense)", 1.71]
    _ior_values["flint_glass_pure"] = ["Flint glass (pure)", 1.61]
    _ior_values["glycerine"] = ["Glycerine", 1.47]
    _ior_values["nacl"] = ["Sodium Chloride", 1.544]
    _ior_values["olive_oil"] = ["Olive Oil", 1.46]
    _ior_values["opal"] = ["Opal", 1.44]
    _ior_values["pet_plastic"] = ["PET plastic", 1.5750]
    _ior_values["plate_glass"] = ["Plate Glass", 1.52]
    _ior_values["polycarbonate"] = ["Polycarbonate", 1.584]
    _ior_values["polystyrene"] = ["Polystyrene", 1.52]
    _ior_values["pyrex_glass"] = ["Pyrex Glass", 1.470]
    _ior_values["quartz"] = ["Quartz", 1.458]
    _ior_values["sapphire"] = ["Sapphire", 1.77]
    _ior_values["silicone_oil_20C"] = ["Silicone Oil @ 20C", 1.4]
    _ior_values["turpentine"] = ["Turpentine", 1.47]
    _ior_values["vacuum"] = ["Vacuum", 1]
    _ior_values["water_20C"] = ["Water @ 20C", 1.330]
    _ior_values["water_ice"] = ["Water Ice", 1.31]

    # A default value that will be assigned an integer index of 0 as required
    # by EnumProperty when using a callback to obtain the list of items.
    default_key = "water_20C"

    def get_sorted_list(self, sort="name"):
        # Make a deep copy of the ior_values dict
        ior_values = copy.deepcopy(self._ior_values)
        # Append a unique integer index to each tuple. The EnumProperty needs
        # this to determine a default item (index 0) when using a callback.
        # Failure to do so results in a random item becoming the default.
        ior_values[self.default_key].append(0)
        index = 1
        for ior in ior_values:
            if ior != self.default_key:
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
        ret = None
        if key not in cls._ior_values.keys():
            print("Error: key '{}' not found in "
                  "LuxCoreIORPresets::get_item()".format(key))
        else:
            ret = cls._ior_values[key]
        return ret

    @classmethod
    def get_value(cls, key=default_key):
        ret = None
        if key not in cls._ior_values.keys():
            print("Error: key '{}' not found in "
                  "LuxCoreIORPresets::get_value()".format(key))
        else:
            ret = cls._ior_values[key][1]
        return ret


# It seems that Blender *Property classes do not support inheritance if
# there are methods in the same class. The following classes
# (LuxCoreIORPresetCommonProperties, LuxCoreIORPresetBase,
#  LUXCORE_OT_ior_preset_names  and LUXCORE_OT_ior_preset_values) are an
# attempt at minimizing code duplication within the limits imposed by Blender.
class LuxCoreIORPresetCommonProperties():
    """ A property-only class to work around Blender's inheritance limits. """
    bl_idname = "luxcore.ior_preset_common_properties"
    bl_label = ""
    node_name = StringProperty()
    node_tree_name = StringProperty()


class LuxCoreIORPresetBase(bpy.types.Operator,
                           LuxCoreIORPresetCommonProperties):
    """ A base class for LUXCORE_OT_ior_preset_* common methods. Do not call"""

    bl_idname = "luxcore.ior_preset_base"

    def cb_ior_preset(self, context):
        return []

    ior_preset = EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)

    def execute(self, context):
        ior = LuxCoreIORPresetValues.get_item(self.ior_preset)
        node_data_path = bpy.data.node_groups[self.node_tree_name].\
            nodes[self.node_name]
        node_data_path.ior_key = self.ior_preset
        node_data_path.ior_name_text = ior[0]
        node_data_path.ior_value_text = str(ior[1])
        node_data_path.ior_value_float = ior[1]
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class LUXCORE_OT_ior_preset_names(LuxCoreIORPresetBase,
                                  LuxCoreIORPresetCommonProperties):
    """ A custom operator to return a list of IOR presets sorted by name """

    bl_idname = "luxcore.ior_preset_names"
    bl_description = "Index of Refraction presets sorted by name"
    bl_property = "ior_preset"
    node_name = StringProperty()
    node_tree_name = StringProperty()

    def cb_ior_preset(self, context):
        preset_list = []
        cl_presets = LuxCoreIORPresetValues()
        preset_list = cl_presets.get_sorted_list("name")
        return preset_list

    ior_preset = EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)


class LUXCORE_OT_ior_preset_values(LuxCoreIORPresetBase,
                                   LuxCoreIORPresetCommonProperties):
    """ A custom operator to return a list of IOR presets sorted by value """

    bl_idname = "luxcore.ior_preset_values"
    bl_description = "Index of Refraction presets sorted by value"
    bl_property = "ior_preset"

    def cb_ior_preset(self, context):
        preset_list = []
        cl_presets = LuxCoreIORPresetValues()
        preset_list = cl_presets.get_sorted_list("value")
        return preset_list

    ior_preset = EnumProperty(name="IOR Preset",
                              description="Index of Refraction Preset Values",
                              items=cb_ior_preset)
