"""Port of src/readWrite/bmCheckDir.m."""

import os


def bmCheckDir(argDir, dlgFlag=True):
    """1 when ``argDir`` is an existing directory, else 0 (no dialog in Python)."""
    if not isinstance(argDir, (str, os.PathLike)):
        return 0
    return 1 if os.path.isdir(argDir) else 0
