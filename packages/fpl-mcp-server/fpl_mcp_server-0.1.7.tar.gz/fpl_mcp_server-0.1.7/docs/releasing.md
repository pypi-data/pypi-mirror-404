# Releasing FPL MCP

This document describes the release process for publishing new versions of FPL MCP to PyPI and GitHub Container Registry.

## Prerequisites

Before creating a release:

1. **PyPI API Token** (one-time setup):
   - Create an account on https://pypi.org if you don't have one
   - Generate an API token: https://pypi.org/manage/account/token/
   - Add it to GitHub repository secrets:
     - Navigate to: Repository Settings → Secrets and variables → Actions
     - Click "New repository secret"
     - Name: `PYPI_API_TOKEN`
     - Value: Your PyPI API token

2. **All tests passing**:
   ```bash
   uv run pytest --cov=src
   ```

3. **Lint checks passing**:
   ```bash
   uv run ruff check src tests
   uv run ruff format --check src tests
   ```

## Release Process

### 1. Update Version

Edit `pyproject.toml` and update the version number:

```toml
[project]
version = "0.2.0"  # Update this
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes, backward compatible

### 2. Update Lockfile

After bumping the version, update the lockfile to match:

```bash
uv lock
```

This ensures the lockfile is synchronized with the new version to prevent CI failures.

### 3. Commit Changes

```bash
git add pyproject.toml uv.lock
git commit -m "chore: bump version to v0.2.0"
git push origin main
```

### 4. Create and Push Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0"

# Push tag to trigger workflows
git push origin v0.2.0
```

### 5. Automated Publishing

The GitHub Actions workflows will automatically:

1. **Build Docker Image** (`.github/workflows/publish-docker.yml`):
   - Build multi-platform images (amd64, arm64)
   - Tag as: `latest`, `v0.2.0`, `v0.2`, `v0`
   - Push to `ghcr.io/nguyenanhducs/fpl-mcp`

2. **Publish to PyPI** (`.github/workflows/publish-pypi.yml`):
   - Build Python package with `uv build`
   - Publish directly with `uv publish`
   - Upload to PyPI

### 6. Verify Release

**Check GitHub Actions**:
- Go to: https://github.com/nguyenanhducs/fpl-mcp/actions
- Verify both "Publish Docker Image" and "Publish to PyPI" workflows succeeded

**Test Docker Image**:
```bash
docker pull ghcr.io/nguyenanhducs/fpl-mcp:latest
docker run --rm -i ghcr.io/nguyenanhducs/fpl-mcp:latest
```

**Test PyPI Package**:
```bash
uvx fpl-mcp-server@0.2.0
```

### 7. Create GitHub Release (Optional)

1. Go to: https://github.com/nguyenanhducs/fpl-mcp/releases
2. Click "Draft a new release"
3. Select the tag you created (`v0.2.0`)
4. Add release notes describing changes
5. Click "Publish release"

## Release Checklist

- [ ] All tests passing
- [ ] Lint checks passing
- [ ] Version bumped in `pyproject.toml`
- [ ] Lockfile updated with `uv lock`
- [ ] Changes committed and pushed to `main`
- [ ] Tag created and pushed
- [ ] GitHub Actions workflows succeeded
- [ ] Docker image verified
- [ ] PyPI package verified
- [ ] GitHub Release created (optional)

## Troubleshooting

**PyPI Upload Failed: "Invalid credentials"**
- Verify `PYPI_API_TOKEN` is set correctly in GitHub secrets
- Regenerate token if needed

**Docker Build Failed**
- Check Dockerfile syntax
- Verify all dependencies are in `pyproject.toml`

**Package Name Conflict on PyPI**
- The package name `fpl-mcp-server` must be unique on PyPI
- If taken, update the name in `pyproject.toml`

## Rolling Back a Release

If you need to remove a bad release:

**PyPI**: You cannot delete releases, but you can yank them:
```bash
pip install twine
twine upload --skip-existing dist/*
# Contact PyPI support to yank: https://pypi.org/help/
```

**Docker**: Delete tags from GitHub Container Registry:
- Go to: https://github.com/nguyenanhducs/fpl-mcp/pkgs/container/fpl-mcp
- Click on the version to delete
- Click "Delete package version"

**Git Tag**: Delete locally and remotely:
```bash
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0
```
