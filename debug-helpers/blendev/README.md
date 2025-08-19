# Blendev Helper

The `blendev` script is a development utility to quickly launch different versions of Blender,
together with different version of the BlendLuxCore source code,
as well as locally compiled versions of LuxCore.

In order to use this script, a few file paths need to be specified in a config file so that the script can locate the correct files on your machine.
- A template for this file is provided as `blendev-config.default`
- Copy this file and rename it to `blendev-config.cfg`
- Change the variables inside this file as appropriate to your system

`blendev-config.cfg` is git-ignored, so that the paths mentionned inside won't
be shared.
As a supplementary measure, if you want to hide your name in paths, you can use
`~` shortcut instead of `/home/your_name`.

After making those changes, simply call the main program `blendev` from the command line.
You can create a symbolic link, for example via `ln -s /PATH/TO/BlendLuxCore/debug-helpers/blendev/blendev ~/.local/bin/blendev`,
or directly add `/path/to/BlendLuxCore/debug-helpers/blendev/blendev` to your PATH environment variable so that the command is always available.

Forther information about the usage are available via the option `blendev -h` or equivalently `blendev --help`.

Currently `blendev` is specifically written for Linux development, adaptations to other operating systems may be written as required.
