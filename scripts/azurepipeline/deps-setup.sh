#!/bin/bash

# Install deps
su -
sudo apt-get -qq update
sudo apt-get install -y git zip wget bzip2 p7zip-full
