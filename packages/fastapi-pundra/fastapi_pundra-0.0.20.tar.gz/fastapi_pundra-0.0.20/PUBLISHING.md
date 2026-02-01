# Publishing Guide for fastapi-pundra with UV

This project now uses `pyproject.toml` and `uv` for package management and publishing.

## Prerequisites

1. **Install UV**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Configure PyPI credentials** (one-time setup):
   ```bash
   # Create PyPI token at https://pypi.org/manage/account/token/
   
   # Option 1: Use environment variables
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=your-pypi-token
   
   # Option 2: Create ~/.pypirc file
   cat > ~/.pypirc << EOF
   [pypi]
   username = __token__
   password = your-pypi-token
   EOF
   chmod 600 ~/.pypirc
   ```

## Development Setup

1. **Install the package in development mode**:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt  # if you have requirements.txt
   # or
   uv pip install requests python-dotenv python-jose bcrypt
   ```

## Version Management

Use the provided script to bump versions:

```bash
# Bump patch version (0.0.19 -> 0.0.20)
python scripts/bump_version.py patch

# Bump minor version (0.0.19 -> 0.1.0)
python scripts/bump_version.py minor

# Bump major version (0.0.19 -> 1.0.0)
python scripts/bump_version.py major

# Set specific version
python scripts/bump_version.py 1.2.3
```

This will update both `pyproject.toml` and `fastapi_pundra/__init__.py`.

## Publishing to PyPI

### Quick Deploy (Recommended)

Simply run the deploy script:

```bash
bash deploy.sh
```

This will:
1. ✅ Clean previous builds
2. ✅ Build the package with `uv build`
3. ✅ Check the package with `twine check`
4. ✅ Upload to PyPI with `twine upload`
5. ✅ Remind you to tag the version

### Manual Steps

If you prefer to run commands manually:

```bash
# 1. Clean previous builds
rm -rf dist/ build/ *.egg-info/

# 2. Build the package
uv build

# 3. Check the package
uvx twine check dist/*

# 4. Upload to PyPI
uvx twine upload dist/*

# 5. Tag the version
git tag -a v0.0.19 -m 'version 0.0.19'
git push --tags
```

### Test PyPI (Recommended before production)

Test your package on Test PyPI first:

```bash
# Build
uv build

# Upload to Test PyPI
uvx twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ fastapi-pundra
```

## Complete Release Workflow

Here's the complete workflow for releasing a new version:

```bash
# 1. Make your changes
git add .
git commit -m "feat: add new feature"

# 2. Bump version
python scripts/bump_version.py patch  # or minor/major

# 3. Review the changes
git diff

# 4. Commit version bump
git commit -am "chore: bump version to X.Y.Z"

# 5. Push to GitHub
git push origin main

# 6. Deploy to PyPI
bash deploy.sh

# 7. The script will remind you to tag - do it:
git tag -a vX.Y.Z -m 'version X.Y.Z'
git push --tags
```

## Building Without Publishing

To build the package without publishing:

```bash
# Build both wheel and sdist
uv build

# Build only wheel
uv build --wheel

# Build only sdist
uv build --sdist
```

The built packages will be in the `dist/` directory.

## Local Installation for Testing

To test the package locally before publishing:

```bash
# Install from local directory
uv pip install .

# Install in editable mode for development
uv pip install -e ".[dev]"

# Install from built wheel
uv pip install dist/fastapi_pundra-0.0.19-py3-none-any.whl
```

## Project Structure

```
fastapi-pundra/
├── pyproject.toml          # Package configuration (replaces setup.py)
├── .python-version         # Python version for uv
├── deploy.sh              # Automated deployment script
├── scripts/
│   └── bump_version.py    # Version management script
├── fastapi_pundra/        # Package source code
│   ├── __init__.py        # Version info
│   └── ...
└── README.md
```

## Key Changes from setup.py

1. **No more `setup.py`**: All configuration is in `pyproject.toml`
2. **Version sync**: Use `bump_version.py` to keep versions in sync
3. **Build backend**: Using `hatchling` (fast, modern, PEP 517 compliant)
4. **UV commands**: Use `uv build` instead of `python setup.py sdist bdist_wheel`
5. **Cleaner process**: No manual cleanup needed (handled by script)

## Troubleshooting

### Issue: "uv: command not found"
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your shell
```

### Issue: "Authentication failed"
```bash
# Make sure your PyPI token is set correctly
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your-pypi-token
```

### Issue: "Package already exists"
```bash
# Bump the version first
python scripts/bump_version.py patch
```

### Issue: Build fails
```bash
# Make sure all dependencies are installed
uv pip install hatchling twine
```

## Additional Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)

