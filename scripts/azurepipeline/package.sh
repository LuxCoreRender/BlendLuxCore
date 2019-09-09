#!/bin/bash

cd release
python3 ./package_releases.py $VERSION_STRING

# cp ./release-$VERSION_STRING/* $BUILD_ARTIFACTSTAGINGDIRECTORY
# cp ./release-$VERSION_STRING-blender2.80/* $BUILD_ARTIFACTSTAGINGDIRECTORY

