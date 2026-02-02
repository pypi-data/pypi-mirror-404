#!/usr/bin/env bash
# Publish script for mediathek-py
# Bumps version, builds, and publishes to PyPI using uv

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${GREEN}==> Publishing mediathek-py${NC}"

# Check if .env file exists
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with PYPI_TOKEN variable"
    exit 1
fi

# Load .env file
set -a
source "${PROJECT_ROOT}/.env"
set +a

# Check if PYPI_TOKEN is set
if [ -z "${PYPI_TOKEN:-}" ]; then
    echo -e "${RED}Error: PYPI_TOKEN not set in .env file${NC}"
    exit 1
fi

# Parse version bump type (default to patch)
BUMP_TYPE="${1:-patch}"

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo -e "${RED}Error: Invalid version bump type: $BUMP_TYPE${NC}"
    echo "Usage: $0 [major|minor|patch]"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep -E '^version = ' "${PROJECT_ROOT}/pyproject.toml" | sed -E 's/version = "(.*)"/\1/')
echo -e "${YELLOW}Current version: ${CURRENT_VERSION}${NC}"

# Calculate new version
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo -e "${GREEN}New version: ${NEW_VERSION}${NC}"

# Confirm with user
read -p "Bump version from ${CURRENT_VERSION} to ${NEW_VERSION} and publish? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Update version in pyproject.toml
echo -e "${YELLOW}==> Updating version in pyproject.toml${NC}"
sed -i.bak -E "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" "${PROJECT_ROOT}/pyproject.toml"
rm "${PROJECT_ROOT}/pyproject.toml.bak"

# Clean previous builds
echo -e "${YELLOW}==> Cleaning previous builds${NC}"
rm -rf "${PROJECT_ROOT}/dist"

# Build with uv
echo -e "${YELLOW}==> Building package with uv${NC}"
cd "${PROJECT_ROOT}"
uv build

# Check if build was successful
if [ ! -d "${PROJECT_ROOT}/dist" ]; then
    echo -e "${RED}Error: Build failed - dist directory not found${NC}"
    exit 1
fi

# Commit version bump
echo -e "${YELLOW}==> Committing version bump${NC}"
git add pyproject.toml
git commit -m "Bump version to ${NEW_VERSION}"
git tag -a "v${NEW_VERSION}" -m "Version ${NEW_VERSION}"

# Publish to PyPI
echo -e "${YELLOW}==> Publishing to PyPI${NC}"
uv publish --token "${PYPI_TOKEN}"

# Push changes and tags
echo -e "${YELLOW}==> Pushing to git repository${NC}"
git push && git push --tags

echo -e "${GREEN}✓ Successfully published version ${NEW_VERSION}!${NC}"
