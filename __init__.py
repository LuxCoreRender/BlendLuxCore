import bpy
import addon_utils
import platform
import os
from shutil import which


_, luxblend_is_enabled = addon_utils.check("luxrender")
if luxblend_is_enabled:
    addon_utils.disable("luxrender", default_set=True)
    print("Disabled the old LuxBlend addon.")
    raise Exception("\n\nThe old LuxBlend addon causes conflicts, "
                    "so it was disabled. Save your user preferences "
                    "and restart Blender before you can enable the "
                    "new addon.")

if platform.system() == "Darwin":
    if bpy.app.version < (2, 82, 7):
        raise Exception("\n\nUnsupported Blender version. 2.82a or higher is required.")
    mac_version = tuple(map(int, platform.mac_ver()[0].split(".")))
    if mac_version < (10, 9, 0):
        raise Exception("\n\nUnsupported Mac OS version. 10.9 or higher is required.")
        
if platform.system() == "Windows":
    # Ensure nvrtc-builtins64_101.dll can be found
    current_dir = os.path.dirname(os.path.realpath(__file__))
    bin_directory = os.path.join(current_dir, "bin")

    from ctypes import windll, c_wchar_p
    from ctypes.wintypes import DWORD

    AddDllDirectory = windll.kernel32.AddDllDirectory
    AddDllDirectory.restype = DWORD
    AddDllDirectory.argtypes = [c_wchar_p]

    os.environ["PATH"] = bin_directory + os.pathsep + os.environ["PATH"]
    AddDllDirectory(bin_directory)

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    
    # Make sure denoiser is executable
    current_dir = os.path.dirname(os.path.realpath(__file__))
    denoiser_path = which(
        'oidnDenoise',
        mode=os.F_OK,
        path=os.path.join(current_dir, "bin")+os.pathsep+os.environ["PATH"]
    )
    if not os.access(denoiser_path, os.X_OK):
        print("Making LuxCore denoiser executable")
        os.chmod(denoiser_path, 0o755)

try:
    from .bin import pyluxcore
except ImportError as error:
    msg = "\n\nCould not import pyluxcore."
    if platform.system() == "Windows":
        msg += ("\nYou probably forgot to install one of the "
                "redistributable packages.\n"
                "They are listed in the release announcement post.")
    elif platform.system() == "Linux":
        if str(error) == "ImportError: libOpenCL.so.1: cannot open shared object file: No such file or directory":
            msg += ("\nYour OpenCL installation is probably missing or broken. "
                    "Look up how to install OpenCL on your system.")
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
    "warning": "beta1",
    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}

from . import auto_load, nodes, properties, handlers
auto_load.init()

from .operators import keymaps


def register():
    auto_load.register()
    nodes.materials.register()
    nodes.textures.register()
    nodes.volumes.register()
    handlers.register()
    keymaps.register()

    from .utils.log import LuxCoreLog
    pyluxcore.Init(LuxCoreLog.add)
    version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}{bl_info["warning"]}'
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")


def unregister():
    keymaps.unregister()
    handlers.unregister()
    nodes.materials.unregister()
    nodes.textures.unregister()
    nodes.volumes.unregister()
    auto_load.unregister()
