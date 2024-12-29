#!/bin/bash

# Called by the "LuxCoreRender.BlendLuxCore" build pipeline
# Deletes the "latest" tag (if existing) from BlendLuxCore git repo, so that it is
# then recreated at the current commit by the following release pipeline.

TAG=$(git tag -l latest)
if [[ $TAG == "latest" ]] ; then
    git remote set-url origin git@github.com:LuxCoreRender/BlendLuxCore.git
    git tag --delete latest
    git push --delete origin latest
fi
