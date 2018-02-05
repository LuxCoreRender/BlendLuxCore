Files that need to be copied from the binary SDK into this directory for releases:

## Linux

* libembree.so.2
* libtbb.so.2
* pyluxcore.so

## Windows

* tbb.dll
* tbbmalloc.dll
* embree.dll
* OpenImageIO.dll
* pyluxcore.pyd

## get_binaries.py

If you have compiled LuxCore yourself, you can use the get_binaries.py Python script to do the work for you:

`python3 get_binaries.py path/to/compiled/files`

It searches the specified path recursively, so you can just pass the top of your compile folder and it searches for all needed files in the subfolders.

If you don't want to be asked if files should be overwritten, call the script with the `--overwrite` argument.
