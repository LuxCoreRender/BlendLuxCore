#!/usr/bin/env bash

# For developers:
# Run this script if you intend to use BLC in editable mode: This script will
# prevent git to track changes to 'wheels' entry in blender_manifest.toml
git config filter.localconfig.clean "sed -E 's/wheels =.*/wheels = []/g'"
git config filter.localconfig.smudge cat
echo "Git filters configured."
