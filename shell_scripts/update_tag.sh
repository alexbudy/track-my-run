#!/bin/bash

# Get the latest Git tag
latest_tag=$(git describe --tags --abbrev=0)

# Get the current value of LATEST_TAG in .env file
current_tag=$(grep '^LATEST_TAG=' .env | sed 's/^LATEST_TAG="//' | sed 's/"$//')

# Check if the latest tag is different from the current one
if [[ "$latest_tag" != "$current_tag" ]]; then
    # Update the environment variable in the .env file
    sed -i "s/^LATEST_TAG=.*/LATEST_TAG=\"$latest_tag\"/" .env
    echo "Updated LATEST_TAG env variable to $latest_tag"
fi


