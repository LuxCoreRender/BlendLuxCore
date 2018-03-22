
### How to create a release

In the release/ folder, there's a python script `package_releases.py`.
You can use it to create the zip files necessary for a release.
It downloads the LuxCore release, extracts the binaries, puts them in BlendLuxCore clones and zips the result.

Call it like this: `./package_releases.py v2.0alpha1`

After it ran through, it should tell you where to find the packaged release .zip archives.
