#!/bin/bash
# Version bump script for timer CLI
# Usage:
#   ./scripts/bump.sh              # Bumps PATCH version (default): 0.1.2 -> 0.1.3
#   TYPE=MINOR ./scripts/bump.sh   # Bumps MINOR version: 0.1.2 -> 0.2.0
#   TYPE=MAJOR ./scripts/bump.sh   # Bumps MAJOR version: 0.1.2 -> 1.0.0

set -e

PYPROJECT="pyproject.toml"

# Get current version
current=$(grep -oP 'version = "\K[0-9]+\.[0-9]+\.[0-9]+' "$PYPROJECT")

if [ -z "$current" ]; then
    echo "Error: Could not find version in $PYPROJECT"
    exit 1
fi

# Parse version components
major=$(echo "$current" | cut -d. -f1)
minor=$(echo "$current" | cut -d. -f2)
patch=$(echo "$current" | cut -d. -f3)

# Determine bump type (default: PATCH)
TYPE=${TYPE:-PATCH}

case "$TYPE" in
    MAJOR)
        major=$((major + 1))
        minor=0
        patch=0
        ;;
    MINOR)
        minor=$((minor + 1))
        patch=0
        ;;
    PATCH)
        patch=$((patch + 1))
        ;;
    *)
        echo "Error: Unknown TYPE '$TYPE'. Use MAJOR, MINOR, or PATCH."
        exit 1
        ;;
esac

new_version="$major.$minor.$patch"

# Update pyproject.toml
sed -i "s/version = \"$current\"/version = \"$new_version\"/" "$PYPROJECT"

echo "Version bumped: $current -> $new_version ($TYPE)"
