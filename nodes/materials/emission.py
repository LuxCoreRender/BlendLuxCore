import math
import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty,
    IntProperty, EnumProperty, PointerProperty
)
from .. import LuxCoreNode
from ...properties.light import (
    POWER_DESCRIPTION, EFFICACY_DESCRIPTION,
    SPREAD_ANGLE_DESCRIPTION, LIGHTGROUP_DESC, IMPORTANCE_DESCRIPTION,
)
from ...properties.ies import LuxCoreIESProps
from ...export import light
from ...ui import icons

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


class LuxCoreNodeMatEmission(LuxCoreNode):
    """
    Emission node.

    Note: this is not a material node.
    The emission node is plugged into a material node.
    It is just a group of values, because otherwise every
    material node would contain dozens of sockets
    """
    bl_label = "Emission"
    bl_width_default = 160

    gain = FloatProperty(name="Gain", default=1, min=0, description="Brightness multiplier")
    power = FloatProperty(name="Power (W)", default=100, min=0, description=POWER_DESCRIPTION)
    efficacy = FloatProperty(name="Efficacy (lm/W)", default=17, min=0, description=EFFICACY_DESCRIPTION)
    ies = PointerProperty(type=LuxCoreIESProps)
    importance = FloatProperty(name="Importance", default=1, min=0, description=IMPORTANCE_DESCRIPTION)
    # We use unit="ROTATION" because angles are radians, so conversion is necessary for the UI
    spread_angle = FloatProperty(name="Spread Angle", default=math.pi / 2, min=0, soft_min=math.radians(5),
                                 max=math.pi / 2, subtype="ANGLE", unit="ROTATION",
                                 description=SPREAD_ANGLE_DESCRIPTION)
    lightgroup = StringProperty(name="Light Group", description=LIGHTGROUP_DESC)
    dls_type_items = [
        ("AUTO", "Auto", DLS_AUTO_DESC, 0),
        ("ENABLED", "Enabled", DLS_ENABLED_DESC, 1),
        ("DISABLED", "Disabled", DLS_DISABLED_DESC, 2),
    ]
    dls_type = EnumProperty(name="DLS", description="Direct Light Sampling Type",
                            items=dls_type_items, default="AUTO")
    # TODO: mapfile and gamma?

    def init(self, context):
        self.add_input("LuxCoreSocketColor", "Color", (1, 1, 1))

        self.outputs.new("LuxCoreSocketMatEmission", "Emission")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "gain")
        col.prop(self, "power")
        col.prop(self, "efficacy")

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
            row.label("Source:")
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

    def export_emission(self, exporter, props, definitions):
        """
        The export method is different because this is not a normal material node.
        It is called from LuxCoreNodeMaterial.export_common_props()
        """
        definitions["emission"] = self.inputs["Color"].export(exporter, props)
        definitions["emission.gain"] = [self.gain] * 3
        definitions["emission.power"] = self.power
        definitions["emission.efficency"] = self.efficacy
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
                exporter.scene.luxcore.errorlog.add_warning(msg)

    def sub_export(self, exporter, props, luxcore_name=None, output_socket=None):
        raise NotImplementedError("This node uses a special export method.")
