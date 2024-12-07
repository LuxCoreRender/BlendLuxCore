version="2.9a1.post5"
platforms=(
  macosx_11_0_arm64
  macosx_10_13_x86_64
  manylinux_2_28_x86_64
  win_amd64
)
for platform in "${platforms[@]}"
do
  echo "Downloading pyluxcore for ${platform}"
  pip download "pyluxcore==${version}" --no-deps --dest ./wheels --only-binary=:all: --python-version=3.11 --platform=$platform
done

# This one for linux distro that would recompile Blender against 3.12 (like ArchLinux)
pip download "pyluxcore==${version}" --no-deps --dest ./wheels --only-binary=:all: --python-version=3.12 --platform=manylinux_2_28_x86_64
