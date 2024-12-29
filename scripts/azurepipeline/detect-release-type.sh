#!/bin/bash

# Called by the "LuxCoreRender.BlendLuxCore" build pipeline
# Detect release type (daily, alpha, beta, RC or final) and set version string
# One, and only one, tag in the form "blendluxcore_v*" is needed, 
# otherwise the official release build aborts.

# Get the branch name from the build environment
BUILD_BRANCH=$(Build.SourceBranchName)
VERSION_TYPE=""

# Print the branch name for debugging
echo "Building branch: $BUILD_BRANCH"

# Determine the release type based on the branch name
if [[ "$BUILD_BRANCH" == "for_blender_4.2" ]]; then
  # Mark the for_blender_4.2 branch as a pre-release
  VERSION_TYPE="pre-release"
  echo "Release type: Pre-release (for_blender_4.2)"
elif [[ "$BUILD_BRANCH" == "master" ]]; then
  # For master branch, it's a final release
  VERSION_TYPE="final"
  echo "Release type: Final (master)"
else
  # Handle other branches as daily builds (could be expanded to alpha/beta/RC in the future)
  VERSION_TYPE="daily"
  echo "Release type: Daily ($BUILD_BRANCH)"
fi

# Check for specific tags (optional)
# Example: If the commit is tagged with a version string (like 'blendluxcore_v1.0.0'), we can use that tag as a version string
if [[ "$(Build.SourceVersion)" =~ "blendluxcore_v" ]]; then
  VERSION_TYPE="official-release"
  echo "Release type: Official release (tag detected)"
fi

# Set the detected version type as an environment variable for later steps in the pipeline
echo "##vso[task.setvariable variable=version_string]$VERSION_TYPE"
echo "Version string set to: $VERSION_TYPE"

# Optionally: If you want to output the version type in a file or use it in subsequent steps, you can add it to a file.
echo "$VERSION_TYPE" > $(Build.ArtifactStagingDirectory)/version.txt

