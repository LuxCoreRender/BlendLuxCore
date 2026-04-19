#!/usr/bin/env python3
"""Retrieve BlendLuxCore version from blender_manifest.toml"""
import tomllib
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", type=Path)
    args = parser.parse_args()

    with open(args.filepath, 'rb') as fp:
        manifest = tomllib.load(fp)
    version = manifest['version']
    print(version, end='')


if __name__ == "__main__":
    main()
