### How to publish a release

#### Using the Azure build system

1. Change version in `__init__.py` (in the `bl_info` dictionary)
2. Commit this change (but don't push yet):  
    `git add -u`  
    `git commit -m "blabla"`
3. Tag the commit with the usual pattern 
    (described [here](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/azure-pipelines.yml)):  
    `git tag -a "blendluxcore_v2.3alpha1"`
4. Push with tags:  
    `git push --follow-tags`
    
This procedure will create a complete github release with everything included.
The steps described below are not necesary in this case, since the Azure script runs `package_releases.py`.

#### Packaging semi-automatically

Use the python script `package_releases.py` in this folder.
It downloads the LuxCore release, extracts the binaries, puts them in BlendLuxCore clones and zips the result.

Call it like this: `./package_releases.py v2.0alpha1`

After it ran through, it should tell you where to find the packaged release .zip archives.
