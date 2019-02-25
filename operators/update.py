import requests
from requests import ConnectionError
import json
import platform
import os
import shutil
import tempfile
import urllib.request
import urllib.error
import zipfile
from collections import OrderedDict

import bpy
from bpy.props import StringProperty, EnumProperty
from ..bin import pyluxcore

GITHUB_API_RELEASE_URL = "https://api.github.com/repos/LuxCoreRender/BlendLuxCore/releases"


class Release:
    # E.g. "v2.0alpha7"
    version_string = ""
    # if it is an unstable (alpha/beta) version
    is_prerelease = False
    download_url = ""


releases = OrderedDict()


def recursive_overwrite(src, dest):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)

        for f in files:
            recursive_overwrite(os.path.join(src, f),
                                os.path.join(dest, f))
    else:
        # Windows does not allow us to delete or replace loaded .dll and .pyd files.
        # However, we can rename them.
        _, extension = os.path.splitext(dest)
        if extension.lower() in {".pyd", ".dll"}:
            dest_old = dest + ".old"
            # If the name we want to use already exists from a previous update,
            # delete the old file (it is not in use anyway)
            if os.path.exists(dest_old):
                os.remove(dest_old)
            if os.path.exists(dest):
                shutil.move(dest, dest_old)

        shutil.copyfile(src, dest)
        # Copy permission bits (rwx)
        shutil.copystat(src, dest)


def get_current_version():
    from .. import bl_info
    version = bl_info["version"]
    # Major.minor version, e.g. "v2.0"
    version_string = "v%d.%d" % (version[0], version[1])
    # alpha/beta suffix, e.g. "alpha7"
    version_string += bl_info["warning"]
    return version_string


callback_strings = []

def release_items_callback(scene, context):
    items = []
    current_version = get_current_version()

    for i, release in enumerate(releases.values()):
        description = ""
        version_string = release.version_string

        if version_string == current_version:
            # A green checkmark to signal the currently installed version
            icon = "FILE_TICK"
            description += " (installed)"
        elif release.is_prerelease:
            icon = "ERROR"
            description += " (unstable)"
        else:
            icon = "NONE"

        items.append((version_string, version_string, description, icon, i))

    # There is a known bug with using a callback,
    # Python must keep a reference to the strings
    # returned or Blender will misbehave or even crash.
    global callback_strings
    callback_strings = items

    return items


class LUXCORE_OT_change_version(bpy.types.Operator):
    bl_idname = "luxcore.change_version"
    bl_label = "Change Version"
    bl_description = "Download a different BlendLuxCore version and replace this installation"

    selected_release = EnumProperty(name="Releases", items=release_items_callback,
                                    description="Select a release")

    def invoke(self, context, event):
        """
        The evoke method fetches the current list of releases from GitHub
        and shows a popup dialog with a dropdown list of versions to the user.
        """
        releases.clear()

        try:
            response_raw = requests.get(GITHUB_API_RELEASE_URL)
        except ConnectionError as error:
            self.report({"ERROR"}, "Connection error")
            return {"CANCELLED"}

        if not response_raw.ok:
            self.report({"ERROR"}, "Response not ok")
            return {"CANCELLED"}

        response = json.loads(response_raw.text or response_raw.content)

        # Info about the currently installed version
        current_is_opencl = not pyluxcore.GetPlatformDesc().Get("compile.LUXRAYS_DISABLE_OPENCL").GetBool()
        system_mapping = {
            "Linux": "linux64",
            "Windows": "win64",
            "Darwin": "mac64"
        }
        try:
            current_system = system_mapping[platform.system()]
        except KeyError:
            self.report({"ERROR"}, "Unsupported system: " + platform.system())
            return {"CANCELLED"}

        for release_info in response:
            entry = Release()
            entry.version_string = release_info["name"].replace("BlendLuxCore ", "")
            entry.is_prerelease = release_info["prerelease"]

            # Assets are the different .zip packages for various OS, with/without OpenCL etc.
            for asset in release_info["assets"]:
                # The name has the form
                # "BlendLuxCore-v2.0alpha7-linux64-opencl.zip" or
                # "BlendLuxCore-v2.0alpha7-linux64.zip" (non-opencl builds)
                middle = asset["name"].replace("BlendLuxCore-", "").replace(".zip", "")
                parts = middle.split("-")
                if len(parts) == 2:
                    version, system = parts
                    is_opencl = False
                elif len(parts) == 3:
                    version, system, _ = parts
                    is_opencl = True
                else:
                    # Older alpha releases used a different naming scheme, we don't support them
                    continue

                if system == current_system and is_opencl == current_is_opencl:
                    # Found the right asset
                    entry.download_url = asset["browser_download_url"]
                    break

            # The asset finding loop may skip entries with old naming scheme, don't include those
            if entry.download_url:
                releases[entry.version_string] = entry

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        """
        The execute method is called when the user clicks the "OK" button.
        It downloads and installs the requested version.
        """
        requested_release = releases[self.selected_release]
        current_version = get_current_version()
        if requested_release.version_string == current_version:
            self.report({"ERROR"}, "This is the currently installed version")
            return {"CANCELLED"}

        print("=======================================")
        print("Changing version to", self.selected_release)
        print("Current version:", current_version)
        print()

        with tempfile.TemporaryDirectory() as temp_dir_path:
            temp_zip_path = os.path.join(temp_dir_path, "default.zip")

            url = requested_release.download_url
            try:
                print("Downloading:", url)
                with urllib.request.urlopen(url, timeout=60) as url_handle, \
                                   open(temp_zip_path, "wb") as file_handle:
                    file_handle.write(url_handle.read())
            except urllib.error.URLError as err:
                self.report({"ERROR"}, "Could not download: %s" % err)
                return {"CANCELLED"}
            print("Download finished")

            current_dir = os.path.dirname(os.path.realpath(__file__))
            # Call dirname twice to go up 2 levels (from addons/BlendLuxCore/operators/)
            blendluxcore_dir = os.path.dirname(current_dir)

            with zipfile.ZipFile(temp_zip_path) as zf:
                print("Extracting zip to", temp_dir_path)
                zf.extractall(temp_dir_path)

            extracted_blendluxcore = os.path.join(temp_dir_path, "BlendLuxCore")
            recursive_overwrite(extracted_blendluxcore, blendluxcore_dir)

        print()
        print("Done. Changed to version", self.selected_release)
        print("Restart Blender for the changes to take effect.")
        print("=======================================")
        # We have to report as error, otherwise we don't get a popup message
        self.report({"ERROR"}, "Restart Blender!")
        return {"FINISHED"}
