"""Siemens twix (.dat) access replacing third_part/twix_for_monalisa/mapVBVD_JH_for_monalisa.

Only what Monalisa uses is exposed: the image counters (NCol, NCha, NLin,
NSeg, NEco), the per-readout time stamps, the parsed header and the raw
readouts in acquisition order (``unsorted()``, ``[NCol, NCha, NAcq]`` like
mapVBVD). Reading relies on ``twixtools`` (by the author of mapVBVD).
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np


class TwixImage:
    def __init__(self, mdbs):
        self._mdbs = mdbs
        heads = [m.mdh for m in mdbs]
        self.NCol = float(max(h.SamplesInScan for h in heads))
        self.NCha = float(max(h.UsedChannels for h in heads))
        self.NLin = float(max(h.Counter.Lin for h in heads) + 1)
        self.NSeg = float(max(h.Counter.Seg for h in heads) + 1)
        self.NEco = float(max(h.Counter.Eco for h in heads) + 1)
        self.timestamp = np.array([[float(h.TimeStamp) for h in heads]])

    def unsorted(self) -> np.ndarray:
        """Readouts ``[NCol, NCha, NAcq]`` (complex single) in acquisition order."""
        data = np.stack([m.data for m in self._mdbs])  # (NAcq, NCha, NCol)
        return np.ascontiguousarray(np.transpose(data, (2, 1, 0))).astype(np.complex64, copy=False)


class Twix:
    def __init__(self, meas):
        self.hdr = meas["hdr"]
        self.image = TwixImage([m for m in meas["mdb"] if m.is_image_scan()])


@lru_cache(maxsize=2)
def _read(path: str, mtime: float) -> Twix:
    import twixtools

    meas = twixtools.read_twix(path, verbose=False)
    return Twix(meas[-1])


def read_twix(path) -> Twix:
    """Last measurement of a twix file (cached while the file is unchanged)."""
    path = os.fspath(path)
    return _read(path, os.path.getmtime(path))
