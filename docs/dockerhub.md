# Monalisa (Python)

[Monalisa](https://github.com/MattechLab/monalisa) reconstructs non-Cartesian and Cartesian MRI
data: gridded, iterative (SENSE, L2, total variation) and motion-compensated chain
reconstructions. This image contains its Python port,
[monalisa-python](https://github.com/MattechLab/monalisa-python), with everything installed:
Python 3.12, NumPy/SciPy/numba, the Siemens and ISMRMRD readers, SimpleITK, the napari viewer,
JupyterLab, the tests and tutorial 1. Only Docker is needed on your computer.

Platforms: `linux/amd64` (Intel/AMD) and `linux/arm64` (Apple silicon, ARM servers).

## Tutorial 1 without cloning the repository

```bash
mkdir -p monalisa/data monalisa/results

# raw data of tutorial 1 (7.9 GB, once)
docker run --rm -v "$PWD/monalisa/data:/data" mattechlab/monalisa-python \
    python demo/data_demo/data_8_tutorial_1/download_data.py --out /data

# JupyterLab on http://127.0.0.1:8888 (open the link with the token printed in the terminal)
docker run --rm -it -p 127.0.0.1:8888:8888 \
    -v "$PWD/monalisa/data:/data" -e MONALISA_TUTORIAL_DATA=/data \
    -v "$PWD/monalisa/results:/work/examples/tutorial_1/results" \
    mattechlab/monalisa-python
```

In JupyterLab, open `examples/tutorial_1/tutorial_1.ipynb`. The results are written to
`monalisa/results` on your computer. Other files changed in the container (the notebook itself)
are lost when it stops: use *File → Download*, or mount a folder of your own
(`-v "$PWD/notebooks:/work/notebooks"`).

The same reconstructions as a script:

```bash
docker run --rm -v "$PWD/monalisa/data:/data" -v "$PWD/monalisa/results:/results" \
    mattechlab/monalisa-python python examples/tutorial_1/tutorial_1.py --data /data --out /results
```

## Your own scripts and notebooks

`import monalisa` works in any folder of the container: mount your project folder on
`/work/mine` (it appears in JupyterLab's file browser, and its files stay on your computer).

```bash
# JupyterLab with your notebooks in mine/ (File → New → Terminal runs scripts there)
docker run --rm -it -p 127.0.0.1:8888:8888 -v "$PWD:/work/mine" mattechlab/monalisa-python

# a script, without JupyterLab
docker run --rm -v "$PWD:/work/mine" -w /work/mine mattechlab/monalisa-python python my_script.py
```

Paths in your code are the container's: mount raw data from elsewhere as well
(`-v /path/to/data:/data:ro`, then read `/data/scan.dat`).

## With a clone of the repository

`docker compose up` in the repository uses the repository folder as the working folder (your
notebooks, code changes and results stay there); see
[docs/docker.md](https://github.com/MattechLab/monalisa-python/blob/main/docs/docker.md).

## Good to know

- **Memory**: tutorial 1 needs about 35 GB. With Docker Desktop (macOS, Windows), raise the memory
  in *Settings → Resources*; `Killed` (exit code 137) means it was too low.
- **Linux**: the container runs as uid 1000; the mounted folders must be writable by that user
  (the first user of the computer usually is). Create them before `docker run`, otherwise Docker
  creates them as root.
- **Images**: in the notebook, `show_image` shows images with sliders. napari windows and
  interactive dialogs need an X11 display; see
  [docs/docker.md](https://github.com/MattechLab/monalisa-python/blob/main/docs/docker.md#windows-napari-viewer-and-interactive-dialogs).
- **Tags**: `latest`, and one tag per release (`0.1.0`, `0.1`). Cite a release tag, or its digest,
  to reproduce a result exactly.

## Links

- Source, documentation and the MATLAB-to-Python name table:
  https://github.com/MattechLab/monalisa-python
- Upstream MATLAB toolbox: https://github.com/MattechLab/monalisa
- License: Apache 2.0
