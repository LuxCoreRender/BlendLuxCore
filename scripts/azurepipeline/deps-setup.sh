#!/bin/bash

# Install deps
sudo apt-get -qq update
sudo apt-get install -y git zip wget bzip2
wget http://neurodebian.ovgu.de/debian/pool/main/p/p7zip/p7zip-full_16.02+dfsg-1~nd14.04+1_amd64.deb
sudo dpkg -i p7zip-full_16.02+dfsg-1~nd14.04+1_amd64.deb
