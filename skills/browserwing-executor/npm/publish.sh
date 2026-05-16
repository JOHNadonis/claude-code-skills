#!/bin/bash
set -e

# NPM Publishing Script for BrowserWing

echo "╔════════════════════════════════════════╗"
echo "║   BrowserWing NPM Publishing Script   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if logged in to npm
if ! npm whoami &> /dev/null; then
  echo "Error: Not logged in to npm"
  echo "Please run: npm login"
  exit 1
fi

# Get version from package.json
VERSION=$(node -p "require('./package.json').version")
echo "Publishing version: $VERSION"
echo ""

# Verify the version matches a GitHub release
echo "Verifying GitHub release exists..."
RELEASE_URL="https://api.github.com/repos/browserwing/browserwing/releases/tags/v${VERSION}"
if ! curl -sf "$RELEASE_URL" > /dev/null; then
  echo "Error: GitHub release v${VERSION} not found"
  echo "Please create a GitHub release first"
  exit 1
fi

echo "✓ GitHub release v${VERSION} found"
echo ""

# Dry run first
echo "Running npm publish --dry-run..."
npm publish --dry-run

echo ""
echo "Ready to publish to npm?"
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled"
  exit 1
fi

# Publish to npm
echo "Publishing to npm..."
npm publish

echo ""
echo "✓ Successfully published browserwing@${VERSION} to npm!"
echo ""
echo "Users can now install with:"
echo "  npm install -g browserwing"
echo "  pnpm add -g browserwing"
