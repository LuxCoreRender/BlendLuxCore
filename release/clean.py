#!/usr/bin/env python3

import os
import shutil

script_dir = os.path.dirname(os.path.realpath(__file__))


if __name__ == "__main__":
    for filename in os.listdir(script_dir):
        if filename.startswith("release-") or filename.endswith(".py"):
            continue

        filepath = os.path.join(script_dir, filename)
        if os.path.isdir(filepath):
            shutil.rmtree(filepath)
        else:
            os.remove(filepath)
