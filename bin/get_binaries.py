
import argparse
from shutil import copy2
import platform
import os

def confirm(message):
    while True:
        confirm = input(message)
        if confirm in ("y", "n"):
            return confirm == "y"
        else:
            print("\nValid answers: y/n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path",
                        help="Source path where the script starts searching for the required files. "
                             "It it traversed recursively.")
    parser.add_argument("--overwrite", help="Overwrite existing files without asking", action="store_true")
    args = parser.parse_args()

    if platform.system() == "Linux":
        files = ["libembree.so.2", "libtbb.so.2", "pyluxcore.so"]
    else:
        files = []

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

            found_files.append(file)

        for found_file in found_files:
            files.remove(found_file)

    for file in files:
        print('ERROR: Could not find file "%s".' % file)