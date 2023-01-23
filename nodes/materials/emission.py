import math
import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty,
    IntProperty, EnumProperty, PointerProperty
)
from ..base import LuxCoreNode
from ...utils.light_descriptions import (
    POWER_DESCRIPTION, EFFICACY_DESCRIPTION, NORMALIZEBYCOLOR_DESCRIPTION,
    SPREAD_ANGLE_DESCRIPTION, LIGHTGROUP_DESC, IMPORTANCE_DESCRIPTION,
    LUMEN_DESCRIPTION, CANDELA_DESCRIPTION, PER_SQUARE_METER_DESCRIPTION,
)
from ...properties.ies import LuxCoreIESProps
from ...export import light
from ...ui import icons
from ...utils.errorlog import LuxCoreErrorLog
from ...utils import node as utils_node

DLS_AUTO_DESC = "Direct light sampling is disabled if the mesh has more than 256 triangles"
DLS_ENABLED_DESC = (
    "Enable direct light sampling: "
    "Trace a shadow ray for each triangle of this mesh (expensive if mesh has many faces). "
    "Use this option if the mesh has more than 256 triangles and is the primary light source in the scene"
)
DLS_DISABLED_DESC = (
    "Disable direct light sampling: "
    "Improves rendering performance of highpoly light emitters if they contribute only little light to the scene"
)


class LuxCoreNodeMatEmission(LuxCoreNode, bpy.types.Node):
    """
    Emission node.

    Note: this is not a material node.
    The emission node is plugged into a material node.
    It is just a group of values, because otherwise every
    material node would contain dozens of sockets
    """
    bl_label = "Emission"
    bl_width_default = 160

    emission_units = [
        ("artistic", "Artistic", "Artist friendly unit using Gain and Exposure", 0),  
        ("power", "Power", "Radiant flux in Watt", 1),
        ("lumen", "Lumen", "Luminous flux in Lumen", 2),
        ("candela", "Candela", "Luminous intensity in Candela", 3)
    ]
    emission_unit: EnumProperty(update=utils_node.force_viewport_update, name="Unit", items=emission_units, default="artistic")
    gain: FloatProperty(update=utils_node.force_viewport_update, name="Gain", default=1, min=0, description="Brightness multiplier")
    exposure: FloatProperty(update=utils_node.force_viewport_update, name="Exposure", default=0, soft_min=-10, soft_max=10, precision=2,
                            description="Power-of-2 step multiplier. An EV step of 1 will double the brightness of the light")
    power: FloatProperty(update=utils_node.force_viewport_update, name="Power (W)", default=100, min=0, description=POWER_DESCRIPTION)
    efficacy: FloatProperty(update=utils_node.force_viewport_update, name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)
    lumen: FloatProperty(update=utils_node.force_viewport_update, name="Lumen", default=1000, min=0, description=LUMEN_DESCRIPTION)
    candela: FloatProperty(update=utils_node.force_viewport_update, name="Candela", default=80, min=0, description=CANDELA_DESCRIPTION)
    per_square_meter: BoolProperty(update=utils_node.force_viewport_update, name="Per square meter", default=False, description=PER_SQUARE_METER_DESCRIPTION)
    normalizebycolor: BoolProperty(update=utils_node.force_viewport_update, name="Normalize by Color Luminance", default=False,
                                    description=NORMALIZEBYCOLOR_DESCRIPTION)
    ies: PointerProperty(update=utils_node.force_viewport_update, type=LuxCoreIESProps)
    importance: FloatProperty(update=utils_node.force_viewport_update, name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle: FloatProperty(update=utils_node.force_viewport_update, name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)
    lightgroup: StringProperty(update=utils_node.force_viewport_update, name="Light Group", description=LIGHTGROUP_DESC)
    dls_type_items = [
        ("AUTO", "Auto", DLS_AUTO_DESC, 0),
        ("ENABLED", "Enabled", DLS_ENABLED_DESC, 1),
        ("DISABLED", "Disabled", DLS_DISABLED_DESC, 2),
    ]
    dls_type: EnumProperty(update=utils_node.force_viewport_update, name="DLS", description="Direct Light Sampling Type",
                            items=dls_type_items, default="AUTO")
    # TODO: mapfile and gamma?

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMatEmission", "Emission")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "emission_unit")
        col = layout.column(align=True)
        if self.emission_unit == "power":
            col.prop(self, "power")
            col.prop(self, "efficacy")
            layout.prop(self, "normalizebycolor")
        elif self.emission_unit == "lumen":
            col.prop(self, "lumen")
            layout.prop(self, "normalizebycolor")
        elif self.emission_unit == "candela":
            col.prop(self, "candela")
            col.prop(self, "per_square_meter")
            layout.prop(self, "normalizebycolor")
        else:
            col.prop(self, "gain")
            col.prop(self, "exposure", slider=True)

        layout.prop(self, "importance")

        lightgroups = context.scene.luxcore.lightgroups
        layout.prop_search(self, "lightgroup",
                           lightgroups, "custom",
                           icon=icons.LIGHTGROUP, text="")

        layout.prop(self, "spread_angle", slider=True)

        # IES Data
        col = layout.column(align=True)
        col.prop(self.ies, "use", toggle=True)

        if self.ies.use:
            box = col.box()

            row = box.row()
            row.label(text="Source:")
            row.prop(self.ies, "file_type", expand=True)

            if self.ies.file_type == "TEXT":
                box.prop(self.ies, "file_text")
                iesfile = self.ies.file_text
            else:
                # self.iesfile_type == "PATH":
                box.prop(self.ies, "file_path")
                iesfile = self.ies.file_path

            sub = box.column(align=True)
            sub.active = bool(iesfile)
            sub.prop(self.ies, "flipz")
            sub.prop(self.ies, "map_width")
            sub.prop(self.ies, "map_height")

        layout.prop(self, "dls_type")

    def export_emission(self, exporter, depsgraph, props, definitions):
        """
        The export method is different because this is not a normal material node.
        It is called from LuxCoreNodeMaterial.export_common_props()
        """
        definitions["emission"] = self.inputs["Color"].export(exporter, depsgraph, props)
        if self.emission_unit == "power":
            definitions["emission.power"] = self.power / ( 2 * math.pi * (1 - math.cos(self.spread_angle/2)) )
            definitions["emission.efficency"] = self.efficacy
            definitions["emission.normalizebycolor"] = self.normalizebycolor
            if self.power == 0 or self.efficacy == 0:
                definitions["emission.gain"] = [0, 0, 0]
            else:
                definitions["emission.gain"] = [1, 1, 1]
        elif self.emission_unit == "lumen":
            definitions["emission.power"] = self.lumen / ( 2 * math.pi * (1 - math.cos(self.spread_angle/2)) )
            definitions["emission.efficency"] = 1.0
            definitions["emission.normalizebycolor"] = self.normalizebycolor
            if self.lumen == 0 :
                definitions["emission.gain"] = [0, 0, 0]
            else:
                definitions["emission.gain"] = [1, 1, 1]    
        elif self.emission_unit == "candela":
            if self.per_square_meter:
                definitions["emission.power"] = 0.0
                definitions["emission.efficency"] = 0
                definitions["emission.gain"] = [self.candela] * 3
                definitions["emission.gain.normalizebycolor"] = self.normalizebycolor
            else:
                definitions["emission.power"] = self.candela * math.pi
                definitions["emission.efficency"] = 1.0
                definitions["emission.normalizebycolor"] = self.normalizebycolor
                if self.candela == 0:
                    definitions["emission.gain"] = [0, 0, 0]
                else:
                    definitions["emission.gain"] = [1, 1, 1]
        else:
            definitions["emission.power"] = 0
            definitions["emission.efficency"] = 0
            definitions["emission.gain"] = [self.gain * pow(2, self.exposure)] * 3
            definitions["emission.normalizebycolor"] = False
            definitions["emission.gain.normalizebycolor"] = False
        definitions["emission.importance"] = self.importance
        definitions["emission.theta"] = math.degrees(self.spread_angle)
        lightgroups = exporter.scene.luxcore.lightgroups
        lightgroup_id = lightgroups.get_id_by_name(self.lightgroup)
        definitions["emission.id"] = lightgroup_id
        exporter.lightgroup_cache.add(lightgroup_id)
        definitions["emission.directlightsampling.type"] = self.dls_type

        if self.ies.use:
            try:
                light.export_ies(definitions, self.ies, self.id_data.library, is_meshlight=True)
            except OSError as error:
                msg = 'Node "%s" in tree "%s": %s' % (self.name, self.id_data.name, error)
                LuxCoreErrorLog.add_warning(msg)

    def sub_export(self, exporter, depsgraph, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("This node uses a special export method.")
