"""Retrieve BlendLuxCore version from blender_manifest.toml"""
import tomllib
import os
from pathlib import Path
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("filepath", type=Path)
args = parser.parse_args()

with open(args.filepath, 'rb') as fp:
    manifest = tomllib.load(fp)
version = manifest['version']
print(version, end='')
