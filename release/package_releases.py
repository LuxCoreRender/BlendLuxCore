#!/usr/bin/env python3

import argparse
import os
import urllib.request
import urllib.error
import subprocess
import shutil
import tarfile
import zipfile

script_dir = os.path.dirname(os.path.realpath(__file__))

# These are the same as in BlendLuxCore/bin/get_binaries.py
# (apart from missing luxcoreui, that's only for developers)
LINUX_FILES = [
    "libembree3.so.3", "libtbb.so.2", "libtbbmalloc.so.2",
    "pyluxcore.so", "pyluxcoretools.zip",
    "libOpenImageDenoise.so.0",
]

WINDOWS_FILES = [
    "embree3.dll", "tbb.dll", "tbbmalloc.dll",
    "OpenImageIO.dll", "pyluxcore.pyd",
    "pyluxcoretool.exe", "pyluxcoretools.zip",
    "OpenImageDenoise.dll",
]

MAC_FILES = [
    "libembree3.dylib", "libembree3.3.dylib", "libtbb.dylib",
    "libtbbmalloc.dylib", "pyluxcore.so",
    "pyluxcoretools.zip", "libomp.dylib",
]

OIDN_WIN = "oidn-windows.zip"
OIDN_LINUX = "oidn-linux.tar.gz"
OIDN_MAC = "oidn-macos.tar.gz"

OIDN_urls = {
    OIDN_WIN: "https://github.com/OpenImageDenoise/oidn/releases/download/v0.9.0/oidn-0.9.0.x64.vc14.windows.zip",
    OIDN_LINUX: "https://github.com/OpenImageDenoise/oidn/releases/download/v0.9.0/oidn-0.9.0.x86_64.linux.tar.gz",
    OIDN_MAC: "https://github.com/OpenImageDenoise/oidn/releases/download/v0.9.0/oidn-0.9.0.x86_64.macos.tar.gz",
}


def print_divider():
    print("=" * 60)


def build_name(prefix, version_string, suffix):
    return prefix + version_string + suffix


def build_zip_name(version_string, suffix):
    return "BlendLuxCore-" + version_string + suffix.split(".")[0]


def extract_files_from_tar(tar_path, files_to_extract, destination):
    # have to use a temp dir (weird extract behaviour)
    temp_dir = os.path.join(script_dir, "temp")
    # Make sure we don't delete someone's beloved temp folder later
    while os.path.exists(temp_dir):
        temp_dir += "_"
    os.mkdir(temp_dir)

    print("Reading tar file:", tar_path)

    tar_type = os.path.splitext(tar_path)[1][1:]
    with tarfile.open(tar_path, "r:" + tar_type) as tar:
        for member in tar.getmembers():
            basename = os.path.basename(member.name)
            if basename not in files_to_extract:
                continue

            # have to use a temp dir (weird extract behaviour)
            print('Extracting "%s" to "%s"' % (basename, temp_dir))
            tar.extract(member, path=temp_dir)
            src = os.path.join(temp_dir, member.name)

            # move to real target directory
            dst = os.path.join(destination, basename)
            print('Moving "%s" to "%s"' % (src, dst))
            if not os.path.isfile(dst):
                shutil.move(src, dst)

    shutil.rmtree(temp_dir)


def extract_files_from_zip(zip_path, files_to_extract, destination):
    # have to use a temp dir (weird extract behaviour)
    temp_dir = os.path.join(script_dir, "temp")
    # Make sure we don't delete someone's beloved temp folder later
    while os.path.exists(temp_dir):
        temp_dir += "_"
    os.mkdir(temp_dir)

    print("Reading zip file:", zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip:
        for member in zip.namelist():
            basename = os.path.basename(member)  # in zip case, member is just a string
            if basename not in files_to_extract:
                continue

            # have to use a temp dir (weird extract behaviour)
            print('Extracting "%s" to "%s"' % (basename, temp_dir))
            src = zip.extract(member, path=temp_dir)

            # move to real target directory
            dst = os.path.join(destination, basename)
            print('Moving "%s" to "%s"' % (src, dst))
            shutil.move(src, dst)

    shutil.rmtree(temp_dir)


def extract_files_from_archive(archive_path, files_to_extract, destination):
    if archive_path.endswith(".zip"):
        extract_files_from_zip(archive_path, files_to_extract, destination)
    elif archive_path.endswith(".tar.gz") or archive_path.endswith(".tar.bz2"):
        extract_files_from_tar(archive_path, files_to_extract, destination)
    else:
        raise Exception("Unknown archive type:", archive_path)


def extract_luxcore_tar(prefix, platform_suffixes, file_names, version_string):
    for suffix in platform_suffixes:
        dst_name = build_zip_name(version_string, suffix)
        destination = os.path.join(script_dir, dst_name, "BlendLuxCore", "bin")

        print()
        print_divider()
        print("Extracting tar to", dst_name)
        print_divider()

        tar_name = build_name(prefix, version_string, suffix)
        extract_files_from_archive(tar_name, file_names, destination)


def extract_luxcore_zip(prefix, platform_suffixes, file_names, version_string):
    for suffix in platform_suffixes:
        dst_name = build_zip_name(version_string, suffix)
        destination = os.path.join(script_dir, dst_name, "BlendLuxCore", "bin")

        print()
        print_divider()
        print("Extracting zip to", dst_name)
        print_divider()

        zip_name = build_name(prefix, version_string, suffix)
        extract_files_from_archive(zip_name, file_names, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version_string",
                        help='E.g. "v2.0alpha1" or "v2.0". Used to download the LuxCore zips')
    args = parser.parse_args()

    # Archives we need.
    url_prefix = "https://github.com/LuxCoreRender/LuxCore/releases/download/luxcorerender_"
    prefix = "luxcorerender-"
    suffixes = [
        "-linux64.tar.bz2",
        "-linux64-opencl.tar.bz2",
        "-win64.zip",
        "-win64-opencl.zip",
        "-mac64.tar.gz",
        "-mac64-opencl.tar.gz",
    ]

    # Download LuxCore binaries for all platforms
    print_divider()
    print("Downloading LuxCore releases")
    print_divider()

    to_remove = []
    for suffix in suffixes:
        name = build_name(prefix, args.version_string, suffix)

        # Check if file already downloaded
        if name in os.listdir(script_dir):
            print('File already downloaded: "%s"' % name)
        else:
            destination = os.path.join(script_dir, name)
            url = url_prefix + args.version_string + "/" + name
            print('Downloading: "%s"' % url)

            try:
                urllib.request.urlretrieve(url, destination)
            except urllib.error.HTTPError as error:
                print(error)
                print("Archive", name, "not available, skipping it.")
                to_remove.append(suffix)

    # Remove suffixes that were not available for download
    for suffix in to_remove:
        suffixes.remove(suffix)

    print()
    print_divider()
    print("Cloning BlendLuxCore")
    print_divider()

    # Clone BlendLuxCore (will later put the binaries in there)
    repo_path = os.path.join(script_dir, "BlendLuxCore")
    if os.path.exists(repo_path):
        # Clone fresh because we delete some stuff after cloning
        print('Destinaton already exists, deleting it: "%s"' % repo_path)
        shutil.rmtree(repo_path)

    clone_args = ["git", "clone", "https://github.com/LuxCoreRender/BlendLuxCore.git"]
    git_process = subprocess.Popen(clone_args)
    git_process.wait()

    # If the current version tag already exists, set the repository to this version
    # This is used in case we re-package a release
    os.chdir("BlendLuxCore")
    tags_raw = subprocess.check_output(["git", "tag", "-l"])
    tags = [tag.decode("utf-8") for tag in tags_raw.splitlines()]

    current_version_tag = "blendluxcore_" + args.version_string
    if current_version_tag in tags:
        print("Checking out tag", current_version_tag)
        subprocess.check_output(["git", "checkout", "tags/" + current_version_tag])

    os.chdir("..")

    # Delete developer stuff that is not needed by users (e.g. tests directory)
    to_delete = [
        os.path.join(repo_path, "tests"),
        os.path.join(repo_path, "doc"),
        os.path.join(repo_path, ".github"),
        os.path.join(repo_path, ".git"),
    ]
    for path in to_delete:
        shutil.rmtree(path)

    print()
    print_divider()
    print("Creating BlendLuxCore release subdirectories")
    print_divider()

    # Create subdirectories for all platforms
    for suffix in suffixes:
        name = build_zip_name(args.version_string, suffix)
        destination = os.path.join(script_dir, name, "BlendLuxCore")
        print('Creating "%s"' % destination)

        if os.path.exists(destination):
            print("(Already exists, cleaning it)")
            shutil.rmtree(destination)

        shutil.copytree(repo_path, destination)

    print()
    print_divider()
    print("Downloading OIDN binaries")
    print_divider()

    for name, url in OIDN_urls.items():
        # Check if file already downloaded
        if name in os.listdir(script_dir):
            print('File already downloaded: "%s"' % name)
        else:
            destination = os.path.join(script_dir, name)
            try:
                urllib.request.urlretrieve(url, destination)
            except urllib.error.HTTPError as error:
                print(error)

    print("Extracting OIDN standalone denoiser")

    for suffix in suffixes:
        name = build_zip_name(args.version_string, suffix)
        destination = os.path.join(script_dir, name, "BlendLuxCore", "bin")

        if "win64" in suffix:
            extract_files_from_archive(OIDN_WIN, ["denoise.exe"], destination)
        elif "linux64" in suffix:
            extract_files_from_archive(OIDN_LINUX, ["denoise"], destination)
        elif "mac64" in suffix:
            extract_files_from_archive(OIDN_MAC, ["denoise"], destination)

    # Linux archives are tar.bz2
    linux_suffixes = [suffix for suffix in suffixes if suffix.startswith("-linux")]
    extract_luxcore_tar(prefix, linux_suffixes, LINUX_FILES, args.version_string)

    # Mac archives are tar.gz
    mac_suffixes = [suffix for suffix in suffixes if suffix.startswith("-mac")]
    extract_luxcore_tar(prefix, mac_suffixes, MAC_FILES, args.version_string)

    # Windows archives are zip
    windows_suffixes = [suffix for suffix in suffixes if suffix.startswith("-win")]
    extract_luxcore_zip(prefix, windows_suffixes, WINDOWS_FILES, args.version_string)

    # Package everything
    print()
    print_divider()
    print("Packaging BlendLuxCore releases")
    print_divider()

    release_dir = os.path.join(script_dir, "release-" + args.version_string)
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.mkdir(release_dir)

    for suffix in suffixes:
        name = build_zip_name(args.version_string, suffix)
        zip_this = os.path.join(script_dir, name)
        print("Zipping:", name)
        zip_name = name + ".zip"

        shutil.make_archive(name, 'zip', zip_this)

        shutil.move(zip_this + ".zip", os.path.join(release_dir, zip_name))

    print()
    print_divider()
    print("Results can be found in: release-" + args.version_string)
    print_divider()


if __name__ == "__main__":
    main()
