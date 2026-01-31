# Publishing Mantisdk to PyPI

This document describes how to set up and publish the Mantisdk package to PyPI.

Mantisdk is part of the Mantis monorepo and is published from `mantisdk/sdk/`.

## Prerequisites

1. A PyPI account (https://pypi.org/account/register/)
2. A TestPyPI account (https://test.pypi.org/account/register/)
3. The package built and ready to publish

## Setting Up Trusted Publishing (Recommended)

Trusted publishing uses OpenID Connect (OIDC) to authenticate with PyPI without needing API tokens.

### Step 1: Reserve the Package Name on PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in the details:
   - **PyPI Project Name**: `mantisdk`
   - **Owner**: Your GitHub organization or username (e.g., `withmetis`)
   - **Repository name**: `mantis`
   - **Workflow name**: `mantisdk-pypi-release.yml`
   - **Environment name**: (leave blank or use `release`)
4. Click "Add"

### Step 2: Set Up TestPyPI (Optional but Recommended)

1. Go to https://test.pypi.org/manage/account/publishing/
2. Follow the same steps as above for TestPyPI (use `mantisdk-pypi-nightly.yml`)

### Step 3: Verify GitHub Actions

The workflows are configured in the mantis repo root `.github/workflows/`:

- `mantisdk-pypi-release.yml` - Publishes to PyPI when you push a tag like `mantisdk-v0.1.0`
- `mantisdk-pypi-nightly.yml` - Publishes nightly builds to TestPyPI
- `mantisdk-test.yml` - Runs tests on changes to `mantisdk/sdk/`

## Manual Publishing (Alternative)

If you need to publish manually:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ mantisdk

# Upload to PyPI
python -m twine upload dist/*
```

## Releasing a New Version

1. Update the version in `mantisdk/sdk/pyproject.toml` and `mantisdk/sdk/src/mantisdk/__init__.py`
2. Commit the changes
3. Create and push a version tag (note the `mantisdk-` prefix):
   ```bash
   git tag mantisdk-v0.1.0
   git push origin mantisdk-v0.1.0
   ```
4. GitHub Actions will automatically build and publish to PyPI

## Version Numbering

We follow semantic versioning (SemVer):

- **MAJOR.MINOR.PATCH** (e.g., `0.1.0`)
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes

## Troubleshooting

### "Project not found" error

Make sure you've set up the pending publisher on PyPI before pushing the first release tag.

### "Authentication failed" error

Verify that:
1. The workflow file name matches what you configured on PyPI
2. The repository owner/name matches
3. The `id-token: write` permission is set in the workflow
