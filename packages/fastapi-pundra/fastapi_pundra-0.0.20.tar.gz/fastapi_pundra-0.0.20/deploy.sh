#!/bin/bash
set -e  # Exit on error

echo "Starting deployment process..."

# Read version from __init__.py
VERSION=$(grep -oP "__version__ = ['\"]([^'\"]+)" fastapi_pundra/__init__.py | grep -oP "[0-9.]+")
echo "📦 Building package version: ${VERSION}"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package using uv
echo "🔨 Building package with uv..."
uv build

# Check the package with twine
echo "🔍 Checking package with twine..."
uvx twine check dist/*

# Publish to PyPI
echo "🚀 Publishing to PyPI..."
uvx twine upload dist/*

# Suggest git tagging
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📌 Don't forget to tag this version:"
echo "   git tag -a v${VERSION} -m 'version ${VERSION}'"
echo "   git push --tags"