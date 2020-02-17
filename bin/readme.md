To see the lists of files that need to be copied from the binary SDK into this directory for releases, look at line 8 in the get_binaries.py script:
https://github.com/LuxCoreRender/BlendLuxCore/blob/master/bin/get_binaries.py#L8

## get_binaries.py

If you have compiled LuxCore yourself, you can use the get_binaries.py Python script to do the work for you:

`python3 get_binaries.py path/to/compiled/files`

It searches the specified path recursively, so you can just pass the top of your compile folder and it searches for all needed files in the subfolders.

If you don't want to be asked if files should be overwritten, call the script with the `--overwrite` argument.
