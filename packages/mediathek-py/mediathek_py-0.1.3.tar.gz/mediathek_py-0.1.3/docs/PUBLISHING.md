# Publishing Workflow

This document describes the automated publishing workflow for mediathek-py.

## Setup (First Time Only)

1. **Get PyPI API Token**
   - Visit https://pypi.org/manage/account/token/
   - Create a new API token with upload permissions
   - Copy the token (starts with `pypi-`)

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env and paste your token:
   # PYPI_TOKEN=pypi-your-actual-token-here
   ```

3. **Verify Setup**

   ```bash
   # Check that script is executable
   ls -l scripts/publish.sh

   # Check that .env exists and is ignored by git
   git status
   ```

## Publishing a New Version

### Quick Reference

```bash
./scripts/publish.sh [major|minor|patch]
```

- **patch** (default): Bug fixes, minor changes (0.1.1 → 0.1.2)
- **minor**: New features, backward compatible (0.1.1 → 0.2.0)
- **major**: Breaking changes (0.1.1 → 1.0.0)

### Step-by-Step

1. **Ensure Clean Working Directory**

   ```bash
   git status
   # Commit or stash any changes
   ```

2. **Run Tests**

   ```bash
   uv run pytest
   ```

3. **Run Publish Script**

   ```bash
   ./scripts/publish.sh patch
   ```

4. **Review and Confirm**
   - Script will show current and new version
   - Type `y` to confirm

5. **Verify Publication**
   - Check https://pypi.org/project/mediathek-py/
   - Verify new version is live

## What the Script Does

The `publish.sh` script automates the entire release process:

1. **Validation**
   - Checks for `.env` file
   - Verifies `PYPI_TOKEN` is set
   - Validates version bump type

2. **Version Bumping**
   - Reads current version from `pyproject.toml`
   - Calculates new version based on bump type
   - Prompts for confirmation

3. **Update and Build**
   - Updates version in `pyproject.toml`
   - Cleans previous builds (`rm -rf dist`)
   - Builds package with `uv build`

4. **Git Operations**
   - Commits version bump
   - Creates annotated git tag (e.g., `v0.1.2`)

5. **Publishing**
   - Publishes to PyPI using `uv publish --token`
   - Pushes commits and tags to remote repository

## Best Practices

### Before Publishing

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG is updated (if you have one)
- [ ] No uncommitted changes

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality (backward compatible)
- **PATCH** version for bug fixes (backward compatible)

### After Publishing

1. Verify package on PyPI
2. Test installation in clean environment:
   ```bash
   uv pip install mediathek-py==X.Y.Z
   ```
3. Update project documentation/website if needed
4. Announce release (GitHub Releases, Twitter, etc.)

## Troubleshooting

### "PYPI_TOKEN not set in .env file"

**Solution:** Create `.env` file with your PyPI token:

```bash
echo "PYPI_TOKEN=pypi-your-token-here" > .env
```

### "Permission denied: ./scripts/publish.sh"

**Solution:** Make script executable:

```bash
chmod +x scripts/publish.sh
```

### Build Fails

**Solution:** Check that all dependencies are installed:

```bash
uv sync
```

### Publish Fails (Authentication Error)

**Solutions:**

1. Verify token is correct in `.env`
2. Check token hasn't expired
3. Verify token has upload permissions for the package

### Git Push Fails

**Solutions:**

1. Pull latest changes: `git pull --rebase`
2. Resolve any conflicts
3. Retry: `git push && git push --tags`

### Wrong Version Published

If you accidentally publish the wrong version:

1. **Cannot delete from PyPI**, but you can:
   - Publish a new corrected version
   - Mark the incorrect version as yanked (prevents new installs)

## Manual Publishing (Fallback)

If the script fails, you can publish manually:

```bash
# 1. Update version in pyproject.toml manually

# 2. Build
uv build

# 3. Publish
uv publish --token pypi-your-token-here

# 4. Commit and tag
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git tag -a "vX.Y.Z" -m "Version X.Y.Z"
git push && git push --tags
```

## Security Notes

- **Never commit** `.env` file to git
- **Never share** your PyPI token
- **Rotate tokens** periodically
- Use **scoped tokens** when possible (limited to specific package)
- Store tokens securely (password manager, encrypted vault)

## Advanced: CI/CD Publishing

For automated publishing via GitHub Actions or similar:

1. Store `PYPI_TOKEN` as repository secret
2. Create workflow that triggers on tags
3. Run build and publish in CI environment

Example GitHub Actions workflow (future enhancement):

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build
      - run: uv publish --token ${{ secrets.PYPI_TOKEN }}
```
