# This is in a separate file because otherwise there are circular imports
from ..engine.base import LuxCoreRenderEngine
from ..ui import icons


def template_refresh_button(is_refreshing, operator_name, layout, run_msg="Refreshing..."):
    col = layout.column()
    col.enabled = LuxCoreRenderEngine.final_running

    col.operator(operator_name, icon=icons.REFRESH)
    if is_refreshing:
        col.label(text=run_msg)
