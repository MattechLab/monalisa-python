"""Port of src/readWrite/bmCreateDir.m."""

import os

from monalisa.io._check_dir import check_dir


def create_dir(argDir, myErrorFlag=False):
    """Create ``argDir``; returns 1 when created, 0 when it already existed."""
    if check_dir(argDir, False):
        if myErrorFlag:
            raise FileExistsError("The directory already exists !")
        return 0
    os.makedirs(argDir)
    return 1
