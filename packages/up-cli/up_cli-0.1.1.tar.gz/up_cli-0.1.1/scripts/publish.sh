#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${GREEN}=== PyPI Publish Script ===${NC}"

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -E '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC}"

# Prompt for new version
read -p "Enter new version (or press Enter to keep $CURRENT_VERSION): " NEW_VERSION

if [ -n "$NEW_VERSION" ]; then
    # Update version in pyproject.toml
    sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
    rm -f pyproject.toml.bak
    echo -e "${GREEN}Version updated to: $NEW_VERSION${NC}"
else
    NEW_VERSION=$CURRENT_VERSION
fi

# Clean previous builds
echo -e "\n${YELLOW}Cleaning previous builds...${NC}"
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Build
echo -e "\n${YELLOW}Building package...${NC}"
python -m build

# Check distribution
echo -e "\n${YELLOW}Checking distribution...${NC}"
twine check dist/*

# Confirm upload
echo -e "\n${YELLOW}Ready to upload version $NEW_VERSION to PyPI${NC}"
read -p "Continue? (y/N): " CONFIRM

if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Uploading to PyPI...${NC}"
    twine upload dist/*
    echo -e "\n${GREEN}Successfully published version $NEW_VERSION to PyPI!${NC}"
    echo -e "Install with: ${YELLOW}pip install up-cli==$NEW_VERSION${NC}"
else
    echo -e "${RED}Upload cancelled.${NC}"
    exit 1
fi
