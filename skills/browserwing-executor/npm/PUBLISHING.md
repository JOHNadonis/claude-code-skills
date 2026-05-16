# NPM Publishing Guide

This document explains how to publish BrowserWing to npm.

## Prerequisites

1. **NPM Account**: Create an account at https://www.npmjs.com
2. **NPM Authentication**: Login via `npm login`
3. **GitHub Release**: Create a GitHub release with binaries first

## Publishing Process

### Manual Publishing

1. **Update Version**
   ```bash
   cd npm
   npm version <new-version>  # e.g., npm version 0.0.2
   ```

2. **Verify Files**
   ```bash
   npm pack --dry-run
   ```

3. **Test Installation Locally**
   ```bash
   npm link
   browserwing --help
   npm unlink
   ```

4. **Publish**
   ```bash
   ./publish.sh
   # Or manually:
   npm publish
   ```

### Automated Publishing (via GitHub Actions)

When you create a new GitHub Release:

1. Tag format: `v0.0.1` (must start with 'v')
2. Upload all platform binaries to the release
3. Publish the release
4. GitHub Actions will automatically:
   - Update package.json version
   - Publish to npm
   - Add comment to release

**Setup Required:**
- Add `NPM_TOKEN` to GitHub Secrets
  1. Generate token at https://www.npmjs.com/settings/[username]/tokens
  2. Go to GitHub repo → Settings → Secrets → New repository secret
  3. Name: `NPM_TOKEN`, Value: your token

## Package Structure

```
npm/
├── package.json          # NPM package manifest
├── install.js           # Post-install script (downloads binary)
├── bin/
│   └── browserwing      # Node wrapper script
├── README.md            # NPM package README
└── .npmignore           # Files to exclude from package
```

## How It Works

1. User runs `npm install -g browserwing`
2. NPM downloads the package (without binaries)
3. `postinstall` script runs (`install.js`)
4. Script detects OS/architecture
5. Downloads appropriate binary from GitHub Releases
6. Places binary in `bin/` directory
7. NPM creates symlink to `bin/browserwing`

## Testing

### Test Local Package

```bash
cd npm
npm pack
npm install -g browserwing-0.0.1.tgz
browserwing --version
npm uninstall -g browserwing
```

### Test Published Package

```bash
npm install -g browserwing
browserwing --version
npm uninstall -g browserwing
```

## Troubleshooting

**Binary not downloading:**
- Check GitHub release exists with correct version
- Verify binary naming: `browserwing-{platform}-{arch}[.exe]`
- Check network/proxy settings

**Permission issues:**
- Use `sudo npm install -g browserwing` on Unix systems
- Or install without `-g` and use `npx browserwing`

**Platform not supported:**
- Check `install.js` platform/arch mappings
- Ensure binaries exist for that platform

## Version Management

- Keep `npm/package.json` version in sync with GitHub releases
- Use semver format: MAJOR.MINOR.PATCH
- Tag releases with 'v' prefix: `v0.0.1`

## Maintenance

**Unpublish a version (within 72 hours):**
```bash
npm unpublish browserwing@0.0.1
```

**Deprecate a version:**
```bash
npm deprecate browserwing@0.0.1 "Critical bug, use 0.0.2+"
```

**Update package info without republishing:**
- Update README, keywords, etc. in package.json
- Publish new patch version

## References

- NPM Publishing: https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry
- Semantic Versioning: https://semver.org/
- Package.json: https://docs.npmjs.com/cli/v10/configuring-npm/package-json
