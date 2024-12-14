import bpy
import platform
import os
from shutil import which

def get_bin_directory():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, "bin")

if bpy.app.version < (2, 93, 0):
    raise Exception("\n\nUnsupported Blender version. 2.93 or higher is required by BlendLuxCore.")

if platform.system() == "Darwin":
    if bpy.app.version < (2, 82, 7):
        raise Exception("\n\nUnsupported Blender version. 2.82a or higher is required.")
    mac_version = tuple(map(int, platform.mac_ver()[0].split(".")))
    if mac_version < (10, 9, 0):
        raise Exception("\n\nUnsupported Mac OS version. 10.9 or higher is required.")
        
if platform.system() == "Windows":
    # Ensure nvrtc-builtins64_101.dll can be found
    bin_directory = get_bin_directory()

    try:
        from ctypes import windll, c_wchar_p
        from ctypes.wintypes import DWORD

        AddDllDirectory = windll.kernel32.AddDllDirectory
        AddDllDirectory.restype = DWORD
        AddDllDirectory.argtypes = [c_wchar_p]

        os.environ["PATH"] = bin_directory + os.pathsep + os.environ["PATH"]
        AddDllDirectory(bin_directory)
    except AttributeError:
        # Windows 7 users might be missing this update
        raise Exception("\n\nYou need to install this update: "
                        "https://www.microsoft.com/en-us/download/details.aspx?id=26764") from None

if platform.system() in {"Linux", "Darwin"}:
    # Required for downloads from the LuxCore Online Library
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    
    # Make sure denoiser is executable
    denoiser_path = which("oidnDenoise", mode=os.F_OK, path=get_bin_directory() + os.pathsep + os.environ["PATH"])
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
    "name": "LuxCoreRender",
    "author": "Simon Wendsche (B.Y.O.B.), Michael Klemm (neo2068), Odilkhan Yakubov (odil24), acasta69, u3dreal, Philstix",
for_blender_4.2
    "version": (2, 9),
    "blender": (4, 2, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    "warning": "beta1",

    "version": (2, 7),
    "blender": (3, 6, 0),
    "category": "Render",
    "description": "LuxCoreRender integration for Blender",
    "warning": "beta2",

    "wiki_url": "https://wiki.luxcorerender.org/",
    "tracker_url": "https://github.com/LuxCoreRender/BlendLuxCore/issues/new",
}

from . import properties, engine, handlers, operators, ui, nodes


def register():
    engine.register()
    handlers.register()
    operators.register()
    properties.register()
    ui.register()
    nodes.register()

    from .utils.log import LuxCoreLog
    pyluxcore.Init(LuxCoreLog.add)
    version_string = f'{bl_info["version"][0]}.{bl_info["version"][1]}{bl_info["warning"]}'
    print(f"BlendLuxCore {version_string} registered (with pyluxcore {pyluxcore.Version()})")


def unregister():
    engine.unregister()
    handlers.unregister()
    operators.unregister()
    properties.unregister()
    ui.unregister()
    nodes.unregister()
