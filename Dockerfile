# syntax=docker/dockerfile:1
#
# Monalisa (Python) with everything installed: numerical stack, raw data readers, registration,
# image viewers (napari, Qt) and JupyterLab. No conda, no pip on the host. See docs/docker.md.
#
#   docker compose up                  # JupyterLab on http://127.0.0.1:8888 (this folder in /work)
#   docker compose run --rm monalisa python examples/tutorial_1/tutorial_1.py --data ... --out ...

FROM python:3.12-slim-trixie

# System libraries of Qt (napari windows, interactive dialogs) for X11, Mesa's software OpenGL
# so that the 2D and 3D views render without a GPU driver in the container, and a virtual
# display (xvfb-run) for the tests of the viewers. xdpyinfo (x11-utils) gives vispy the screen's
# DPI (otherwise it warns "could not determine DPI").
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tini xvfb xauth x11-utils \
        libgl1 libegl1 libegl-mesa0 libopengl0 libglx-mesa0 libgl1-mesa-dri \
        libglib2.0-0t64 libfontconfig1 libfreetype6 libdbus-1-3 \
        libx11-6 libx11-xcb1 libxext6 libxrender1 libxi6 libxkbcommon0 libxkbcommon-x11-0 \
        libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 \
        libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

# OpenGL of the napari windows. Without a GPU, Mesa's software renderer: on a host with an NVIDIA
# card Mesa would otherwise try the absent nouveau driver and hang while napari creates its canvas.
# On such a host, Mesa cannot draw into windows of the NVIDIA X server: `docker run --gpus all`
# (NVIDIA Container Toolkit) brings the host's NVIDIA OpenGL instead, which the capabilities below
# enable (the software setting does not apply to it).
ENV LIBGL_ALWAYS_SOFTWARE=1 \
    NVIDIA_DRIVER_CAPABILITIES=graphics,utility \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Files written to mounted folders belong to uid 1000, the first user on most Linux systems.
RUN useradd --create-home --uid 1000 --shell /bin/bash monalisa
WORKDIR /work

# Dependencies first, from pyproject.toml: this layer is rebuilt only when they change. No heredoc
# (RUN <<EOF): builders without heredoc support (legacy builder, some VS Code dev container builds)
# would silently run nothing and give an image without the libraries. The final import fails the
# build if they are missing.
COPY pyproject.toml /tmp/pyproject.toml
RUN python -c "import tomllib; \
p = tomllib.load(open('/tmp/pyproject.toml', 'rb'))['project']; \
extras = [d for e in ('io', 'reg', 'notebook', 'test') for d in p['optional-dependencies'][e]]; \
print('\n'.join(p['dependencies'] + [d for d in extras if not d.startswith('monalisa-python')]))" \
        > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt \
    && python -c "import numpy, scipy, numba, h5py, napari, ipykernel, jupyterlab"

# The repository, installed in editable mode: when a folder is mounted on /work (compose.yaml),
# its code is the one that runs.
COPY --chown=monalisa:monalisa . /work
RUN pip install --no-deps -e /work

USER monalisa
EXPOSE 8888
ENTRYPOINT ["tini", "--"]
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/work"]
