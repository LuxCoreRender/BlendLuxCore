#!/usr/bin/env python3

import glob
import subprocess
import sys
import os

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

exit(status)
