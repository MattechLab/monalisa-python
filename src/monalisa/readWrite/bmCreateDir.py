"""Port of src/readWrite/bmCreateDir.m."""

import os

from monalisa.readWrite.bmCheckDir import bmCheckDir


def bmCreateDir(argDir, myErrorFlag=False):
    """Create ``argDir``; returns 1 when created, 0 when it already existed."""
    if bmCheckDir(argDir, False):
        if myErrorFlag:
            raise FileExistsError("The directory already exists !")
        return 0
    os.makedirs(argDir)
    return 1
