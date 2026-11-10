# syntax=docker/dockerfile:1
#
# Monalisa (Python) with everything installed: numerical stack, raw data readers, registration,
# image viewers (napari, Qt) and JupyterLab. No conda, no pip on the host. See docs/docker.md.
#
#   docker compose up                  # JupyterLab on http://127.0.0.1:8888 (this folder in /work)
#   docker compose run --rm monalisa python examples/tutorial_1/tutorial_1.py --data ... --out ...

FROM python:3.12-slim-bookworm

# System libraries of Qt (napari windows, interactive dialogs) for X11, Mesa's software OpenGL
# so that the 2D and 3D views render without a GPU driver in the container, and a virtual
# display (xvfb-run) for the tests of the viewers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tini xvfb xauth \
        libgl1 libegl1 libegl-mesa0 libopengl0 libglx-mesa0 libgl1-mesa-dri \
        libglib2.0-0 libfontconfig1 libfreetype6 libdbus-1-3 \
        libx11-6 libx11-xcb1 libxext6 libxrender1 libxi6 libxkbcommon0 libxkbcommon-x11-0 \
        libxcb1 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 \
        libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Files written to mounted folders belong to uid 1000, the first user on most Linux systems.
RUN useradd --create-home --uid 1000 --shell /bin/bash monalisa
WORKDIR /work

# Dependencies first, from pyproject.toml: this layer is rebuilt only when they change.
COPY pyproject.toml /tmp/pyproject.toml
RUN python - <<'EOF' > /tmp/requirements.txt
import tomllib
project = tomllib.load(open("/tmp/pyproject.toml", "rb"))["project"]
deps = list(project["dependencies"])
for extra in ("io", "reg", "notebook", "test"):
    deps += [d for d in project["optional-dependencies"][extra] if not d.startswith("monalisa-python")]
print("\n".join(deps))
EOF
RUN pip install -r /tmp/requirements.txt

# The repository, installed in editable mode: when a folder is mounted on /work (compose.yaml),
# its code is the one that runs.
COPY --chown=monalisa:monalisa . /work
RUN pip install --no-deps -e /work

USER monalisa
EXPOSE 8888
ENTRYPOINT ["tini", "--"]
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/work"]
