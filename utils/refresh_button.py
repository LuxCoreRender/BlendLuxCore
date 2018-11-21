# This is in a separate file because otherwise there are circular imports
from ..engine import LuxCoreRenderEngine
from ..ui import icons


def template_refresh_button(data, property_name, layout, run_msg="Refreshing..."):
    row = layout.row()
    row.enabled = LuxCoreRenderEngine.final_running

    if getattr(data, property_name):
        row.label(run_msg)
    else:
        row.prop(data, property_name, toggle=True, icon=icons.REFRESH)
