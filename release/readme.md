How to publish a release (using the Azure build system):

1. Change version in `__init__.py` (in the `bl_info` dictionary)
2. Commit this change (but don't push yet):  
    `git add -u`  
    `git commit -m "blabla"`
3. Tag the commit with the usual pattern 
    (described [here](https://github.com/LuxCoreRender/BlendLuxCore/blob/master/azure-pipelines.yml)):  
    `git tag -a "blendluxcore_v2.3alpha1"`
4. Push with tags:  
    `git push --follow-tags`
