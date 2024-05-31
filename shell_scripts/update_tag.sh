#!/bin/bash

# Get the latest Git tag
latest_tag=$(git describe --tags --abbrev=0)

# Update the environment variable in the .env file
sed -i "s/^LATEST_TAG=.*/LATEST_TAG=\"$latest_tag\"/" .env

