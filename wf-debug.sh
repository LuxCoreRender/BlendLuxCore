#!/bin/bash

# This script is a helper for local debugging of github workflow scripts.
# It is primarily intended to run on Linux platform and requires 'nektos/act'

act workflow_dispatch --workflows .github/workflows/release_bundle.yml -P ubuntu-latest=catthehacker/ubuntu:act-latest --action-offline-mode -s GITHUB_TOKEN="$(gh auth token)" --artifact-server-path /tmp/blendluxcore
