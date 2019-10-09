#!/bin/bash

cd release
python3 ./package_releases.py $VERSION_STRING

cp ./release-$VERSION_STRING/* $BUILD_ARTIFACTSTAGINGDIRECTORY
