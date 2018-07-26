#!/usr/bin/env python3

import glob
import subprocess
import sys
import os

ANSI_RESET = "\033[0m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"

blender_executable = "blender"

# allow override of blender executable (important for CI!)
if len(sys.argv) > 1:
    blender_executable = sys.argv[1]

if not os.path.exists(blender_executable):
    print("Could not find Blender executable at path:", blender_executable)
    exit(1)

# iterate over each *.test.blend file in the "tests" directory
# and open up blender with the .test.blend file and the corresponding .test.py python script
status = 0
failed = []

for blend_file in glob.glob("./**/*.test.blend"):
    test_name = os.path.splitext(os.path.basename(blend_file))[0]

    print("\n\n")
    print("=" * 40)
    print(test_name)
    print("=" * 40)

    args = [blender_executable, "--addons", "BlendLuxCore", "--factory-startup", "-noaudio",
            "-b", blend_file, "--python", blend_file.replace(".blend", ".py")]
    return_code = subprocess.call(args)

    if return_code != 0:
        # Log the error, but continue testing
        status = return_code
        failed.append(test_name)
        print(ANSI_RED + "Test " + test_name + " failed! (returned " + str(return_code) + ")" + ANSI_RESET)

# Show summary
print("\n\n")
print("=" * 40)
print("  Summary:")
print("=" * 40)
print()

if failed:
    print(ANSI_RED + "Failed tests:" + ANSI_RESET)
    print()

    for test_name in failed:
        print(ANSI_RED + "* " + test_name + ANSI_RESET)
else:
    print(ANSI_GREEN + "All tests successful." + ANSI_RESET)

print()

exit(status)
