import bl_ui
from bl_ui.properties_render import RenderButtonsPanel
import bpy
from bpy.types import Panel


class LuxCoreConfig(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = "LUXCORE"
    bl_label = "LuxCore Config"

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "LUXCORE"

    def draw(self, context):
        layout = self.layout
        config = context.scene.luxcore.config

        # Device
        row_device = layout.row()
        row_device.enabled = config.engine == "PATH"
        row_device.label("Device:")

        if config.engine == "PATH":
            row_device.prop(config, "device", expand=True)
        else:
            row_device.prop(config, "bidir_device", expand=True)

        # Engine
        row_engine = layout.row()
        row_engine.label("Engine:")
        row_engine.prop(config, "engine", expand=True)

        if config.engine == "PATH":
            # Path options
            layout.prop(config, "tiled")

            if config.tiled:
                layout.label("Tiled path uses special sampler", icon="INFO")
            else:
                row_sampler = layout.row()
                row_sampler.label("Sampler:")
                row_sampler.prop(config, "sampler", expand=True)
        else:
            # Bidir options
            row_sampler = layout.row()
            row_sampler.enabled = False
            row_sampler.label("Sampler:")
            row_sampler.prop(config, "bidir_sampler", expand=True)
