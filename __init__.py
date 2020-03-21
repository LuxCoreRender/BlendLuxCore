import bpy
import addon_utils

_, luxblend_is_enabled = addon_utils.check("luxrender")
if luxblend_is_enabled:
    addon_utils.disable("luxrender", default_set=True)
    print("Disabled the old LuxBlend addon.")
    raise Exception("\n\nThe old LuxBlend addon causes conflicts, "
                    "so it was disabled. Save your user preferences "
                    "and restart Blender before you can enable the "
                    "new addon.")

try:
    from .bin import pyluxcore
except ImportError as error:
    msg = "\n\nCould not import pyluxcore."
    import platform
    if platform.system() == "Windows":
        msg += ("\nYou probably forgot to install one of the "
                "redistributable packages.\n"
                "They are listed in the release announcement post.")
    # Raise from None to suppress the unhelpful
    # "during handling of the above exception, ..."
    raise Exception(msg + "\n\nImportError: %s" % error) from None

bl_info = {
    "name": "LuxCore",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Philstix",
    "version": (2, 4),
    "blender": (2, 80, 0),
    "category": "Render",
    "location": "Info header, render engine menu",
    "description": "LuxCore integration for Blender",
    "warning": "alpha0",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}

from . import auto_load, nodes, properties, handlers
auto_load.init()


addon_keymaps = []


def register():
    auto_load.register()
    nodes.materials.register()
    nodes.textures.register()
    nodes.volumes.register()
    handlers.register()

    from .utils.log import LuxCoreLog
    pyluxcore.Init(LuxCoreLog.add)
    version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}{bl_info["warning"]}'
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")

    # Keymaps
    wm = bpy.context.window_manager
    keymap = wm.keyconfigs.addon.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")

    from .operators.node_editor import LUXCORE_OT_node_editor_viewer
    keymap_item = keymap.keymap_items.new(LUXCORE_OT_node_editor_viewer.bl_idname, 'LEFTMOUSE', 'PRESS', ctrl=True, shift=True)

    addon_keymaps.append((keymap, keymap_item))


def unregister():
    handlers.unregister()
    nodes.materials.unregister()
    nodes.textures.unregister()
    nodes.volumes.unregister()
    auto_load.unregister()

    # Keymaps
    for keymap, keymap_item in addon_keymaps:
        keymap.keymap_items.remove(keymap_item)
    addon_keymaps.clear()
