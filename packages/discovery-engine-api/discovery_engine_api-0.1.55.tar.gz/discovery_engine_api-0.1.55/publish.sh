#!/bin/bash
# Script to build and publish discovery-engine-api to PyPI
#
# Usage:
#   ./publish.sh [test|prod]
#
# Authentication:
#   For local publishing, use API tokens (trusted publishing only works in GitHub Actions):
#   export TWINE_USERNAME=__token__
#   export TWINE_PASSWORD=pypi-xxxxxxxxxxxxx
#
#   Or use keyring: python -m keyring set https://test.pypi.org/legacy/ __token__
#
#   Note: Trusted Publishing (OIDC) is configured for GitHub Actions workflows.
#   For automated publishing, push to staging branch to trigger TestPyPI publish,
#   or push a release tag to trigger PyPI publish.
#
# Before publishing:
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG if needed
# 3. Commit and tag the release
# 4. Run: ./publish.sh test  (to test on TestPyPI)
# 5. Run: ./publish.sh prod  (to publish to PyPI)

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Are you in the client package directory?"
    exit 1
fi

# Determine which PyPI to use
if [ "$1" == "test" ]; then
    REPOSITORY="--repository testpypi"
    echo "Publishing to TestPyPI..."
elif [ "$1" == "prod" ]; then
    REPOSITORY=""
    echo "Publishing to PyPI (production)..."
else
    echo "Usage: $0 [test|prod]"
    echo "  test - Publish to TestPyPI"
    echo "  prod - Publish to PyPI (production)"
    exit 1
fi

# Check for required tools
if ! command -v python &> /dev/null; then
    echo "Error: python not found"
    exit 1
fi

# Install build tools
echo "Installing build tools..."
python -m pip install --upgrade build twine

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Build the package
echo "Building package..."
python -m build

# Check the build
echo "Checking built package..."
python -m twine check dist/*

# Upload
echo "Uploading to PyPI..."
if [ "$1" == "test" ]; then
    python -m twine upload $REPOSITORY dist/*
else
    echo "⚠️  WARNING: You are about to publish to PRODUCTION PyPI!"
    echo "Press Ctrl+C to cancel, or Enter to continue..."
    read
    python -m twine upload $REPOSITORY dist/*
fi

echo "✅ Package published successfully!"
echo ""
echo "Users can now install with:"
echo "  pip install discovery-engine-api"
echo "  pip install discovery-engine-api[pandas]"
