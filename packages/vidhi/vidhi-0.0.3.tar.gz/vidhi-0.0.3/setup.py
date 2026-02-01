"""Setup script for vidhi package.

This uses setuptools_scm to determine version from git tags.
Following the vajra pattern for version handling.
"""

import os
import sys
from datetime import datetime

from setuptools import setup
from setuptools_scm import get_version


def get_vidhi_version() -> str:
    """Get version string, handling release and nightly builds for PyPI compatibility."""
    version = get_version(
        write_to="vidhi/_version.py",
    )

    is_nightly_build = os.getenv("IS_NIGHTLY_BUILD", "false") == "true"

    if is_nightly_build:
        # For nightly builds, use date-based dev version
        # e.g., 0.0.4.dev12+g6833d6f -> 0.0.4.dev20260131
        base = version.split(".dev")[0] if ".dev" in version else version.split("+")[0]
        version = f"{base}.dev{datetime.now().strftime('%Y%m%d%H')}"
    else:
        # For release builds, use clean version (no dev suffix, no local part)
        # e.g., 0.0.4.dev12+g6833d6f -> 0.0.4
        # e.g., 0.0.3+g1234567 -> 0.0.3
        # e.g., 0.0.3 -> 0.0.3
        if ".dev" in version:
            version = version.split(".dev")[0]
        elif "+" in version:
            version = version.split("+")[0]

    return version


setup(
    version=get_vidhi_version(),
)
