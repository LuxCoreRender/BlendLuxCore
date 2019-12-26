#!/bin/bash

# Install deps
sudo apt-get -qq update
sudo apt-get install -y git zip wget bzip2
echo "deb http://neurodebian.ovgu.de/debian/ trusty main contrib non-free" | sudo tee -a /etc/apt/sources.list
sudo apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 0xA5D32F012649A5A9
sudo apt-get update
sudo apt-get install p7zip-full