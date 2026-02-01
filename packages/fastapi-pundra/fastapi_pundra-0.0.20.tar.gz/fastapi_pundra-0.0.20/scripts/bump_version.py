#!/usr/bin/env python3
"""
Script to bump version in both pyproject.toml and __init__.py
Usage: python scripts/bump_version.py [major|minor|patch] or python scripts/bump_version.py <version>
"""
import re
import sys
from pathlib import Path


def get_current_version():
    """Read current version from __init__.py"""
    init_file = Path("fastapi_pundra/__init__.py")
    content = init_file.read_text()
    match = re.search(r"__version__ = ['\"]([^'\"]+)['\"]", content)
    if match:
        return match.group(1)
    raise ValueError("Version not found in __init__.py")


def bump_version(version_str, bump_type):
    """Bump version based on type (major, minor, patch)"""
    major, minor, patch = map(int, version_str.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch")
    
    return f"{major}.{minor}.{patch}"


def update_version_in_file(file_path, pattern, replacement):
    """Update version in a file using regex pattern"""
    content = Path(file_path).read_text()
    updated = re.sub(pattern, replacement, content)
    Path(file_path).write_text(updated)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py [major|minor|patch] or python scripts/bump_version.py <version>")
        sys.exit(1)
    
    arg = sys.argv[1]
    current_version = get_current_version()
    
    # Check if arg is a version number or bump type
    if re.match(r'^\d+\.\d+\.\d+$', arg):
        new_version = arg
    elif arg in ['major', 'minor', 'patch']:
        new_version = bump_version(current_version, arg)
    else:
        print(f"Error: Invalid argument '{arg}'. Use major/minor/patch or a version like 1.0.0")
        sys.exit(1)
    
    print(f"📦 Bumping version: {current_version} → {new_version}")
    
    # Update __init__.py
    update_version_in_file(
        "fastapi_pundra/__init__.py",
        r"__version__ = ['\"]([^'\"]+)['\"]",
        f"__version__ = '{new_version}'"
    )
    print(f"✅ Updated fastapi_pundra/__init__.py")
    
    # Update pyproject.toml
    update_version_in_file(
        "pyproject.toml",
        r'version = "[^"]+"',
        f'version = "{new_version}"'
    )
    print(f"✅ Updated pyproject.toml")
    
    print(f"\n🎉 Version bumped successfully to {new_version}")
    print("\n📝 Next steps:")
    print(f"   1. Review changes: git diff")
    print(f"   2. Commit changes: git commit -am 'Bump version to {new_version}'")
    print(f"   3. Deploy: bash deploy.sh")


if __name__ == "__main__":
    main()

