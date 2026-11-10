"""Access to ISMRMRD (.mrd, HDF5) files as read by upstream with h5read."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import h5py
import numpy as np


def read_mrd(path):
    """``(head, data, xml)``: acquisition header fields, the list of interleaved
    real/imag float32 readouts and the XML header string."""
    with h5py.File(path, "r") as f:
        acq = f["/dataset/data"][()]
        xml = f["/dataset/xml"][()]
    xml = xml[0] if np.ndim(xml) else xml
    xml = xml.decode() if isinstance(xml, bytes) else str(xml)
    return acq["head"], acq["data"], xml


def fov(xml: str, space: str) -> np.ndarray:
    """``[x, y, z]`` of ``<space><fieldOfView_mm>`` in the XML header (namespace agnostic)."""
    root = ET.fromstring(xml)
    for el in root.iter():
        if el.tag.split("}")[-1] == space:
            for sub in el:
                if sub.tag.split("}")[-1] == "fieldOfView_mm":
                    vals = {c.tag.split("}")[-1]: float(c.text) for c in sub}
                    return np.array([vals["x"], vals["y"], vals["z"]])
    raise ValueError(f"No {space}/fieldOfView_mm in the ISMRMRD header")


def readouts(data, N: int, nCh: int, nLine: int, dtype=np.complex128) -> np.ndarray:
    """Readouts ``[N, nCh, nLine]`` from the interleaved float32 acquisition data."""
    out = np.zeros((N, nCh, nLine), dtype=dtype)
    for i in range(nLine):
        acq = np.reshape(np.asarray(data[i], dtype=np.float32), (2, N, nCh), order="F")
        out[:, :, i] = acq[0] + 1j * acq[1]
    return out
