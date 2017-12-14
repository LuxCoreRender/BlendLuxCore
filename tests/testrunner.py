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
for file in glob.glob("./**/*.test.blend"):
  subprocess.call([blender_executable, "--addons", "BlendLuxCore",
                   "--factory-startup", "-noaudio", "-b", file, "--python",
                   file.replace(".blend", ".py")])
