#!/bin/bash

# Install deps
sudo apt-get -qq update
#sudo apt-get install -y wget libtool git cmake3 g++ flex bison libbz2-dev libopenimageio-dev libtiff5-dev libpng12-dev libgtk-3-dev libopenexr-dev libgl1-mesa-dev python3-dev python3-pip python3-numpy ocl-icd-opencl-dev
sudo apt-get install -y git zip wget bzip2

# Copy pipeline scripts to have them available for all branches
# mkdir ../scripts
# cp -R ./scripts/* ../scripts/
