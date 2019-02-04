#!/usr/bin/env python3

import argparse
from shutil import copy2
import platform
import os

LINUX_FILES = [
    "libembree3.so.3", "libtbb.so.2", "libtbbmalloc.so.2",
    "pyluxcore.so", "luxcoreui", "pyluxcoretools.zip",
    "libOpenImageDenoise.so.0",
]

WINDOWS_FILES = [
    "embree3.dll", "tbb.dll", "tbbmalloc.dll",
    "OpenImageIO.dll", "pyluxcore.pyd", "luxcoreui.exe",
    "pyluxcoretool.exe", "pyluxcoretools.zip",
    "OpenImageDenoise.dll",
]

MAC_FILES = [
    "libembree3.dylib", "libembree3.3.dylib", "libtbb.dylib",
    "libtbbmalloc.dylib", "pyluxcore.so", "luxcoreui",
    "pyluxcoretools.zip", "libomp.dylib",
]


def confirm(message):
    while True:
        response = input(message)
        if response in ("y", "n"):
            return response == "y"
        else:
            print("\nValid answers: y/n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path",
                        help="Source path where the script starts searching for the required files. "
                             "It it traversed recursively.")
    parser.add_argument("--overwrite", help="Overwrite existing files without asking", action="store_true")
    args = parser.parse_args()

    if platform.system() == "Linux":
        files = LINUX_FILES
    elif platform.system() == "Windows":
        files = WINDOWS_FILES
    elif platform.system() == "Darwin":
        files = MAC_FILES
    else:
        print("Unsupported system:", platform.system())

    for root, dirnames, filenames in os.walk(args.source_path):
        files_in_dir = set(filenames).intersection(files)
        found_files = []

        for file in files_in_dir:
            src = os.path.join(root, file)
            script_dir = os.path.dirname(os.path.realpath(__file__))
            dst = os.path.join(script_dir, file)

            # Check if the file is already in BlendLuxCore/bin folder
            if os.path.isfile(dst):
                if args.overwrite or confirm("Overwrite " + file + "? (y/n): "):
                    os.remove(dst)
                    print("Copying", file, "from", root)
                    copy2(src, dst)
                else:
                    print("Skipping file", file)
            else:
                print("Copying", file, "from", root)
                copy2(src, dst)

            found_files.append(file)

        for found_file in found_files:
            files.remove(found_file)

    for file in files:
        print('ERROR: Could not find file "%s".' % file)


if __name__ == "__main__":
    main()
