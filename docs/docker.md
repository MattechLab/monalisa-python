# Running Monalisa in Docker

The image built from [`Dockerfile`](../Dockerfile) contains everything needed to run the package,
the tutorial and the tests: Python 3.12, the dependencies of `pyproject.toml` with all extras
(`io`: Siemens and ISMRMRD readers; `reg`: SimpleITK; `notebook`: JupyterLab; `test`: pytest),
napari with the Qt and OpenGL system libraries, and the repository installed in editable mode.
Nothing but Docker is installed on the computer: no conda, no pip, no system libraries.

MATLAB is not in the image (it needs a licence): the MATLAB recordings used by the parity tests
are made outside the container with `tools/matlab_capture`, then replayed inside it.

## Start

From the repository folder:

```bash
docker compose up
```

The first run builds the image (a few minutes, about 3 GB); later runs start in seconds. Open the
`http://127.0.0.1:8888/lab?token=...` link printed in the terminal. Stop with Ctrl+C, or
`docker compose down` from another terminal. After a `git pull` that changes the dependencies
(`pyproject.toml`) or the `Dockerfile`, rebuild with `docker compose build`.

[`compose.yaml`](../compose.yaml) mounts the repository folder on `/work` in the container, so:

- notebooks, code changes and results are files of the repository folder on the computer;
- the code that runs is the one in the folder (editable install): no rebuild after editing `src/`;
- JupyterLab only listens on `127.0.0.1` (this computer) and asks for its token.

Without compose, the same container is:

```bash
docker build -t monalisa-python .
docker run --rm -it -p 127.0.0.1:8888:8888 -v "$PWD":/work monalisa-python
```

## Commands

Any command runs in a fresh container with `docker compose run --rm monalisa <command>`
(working directory: the repository):

```bash
# tutorial 1: data (7.9 GB, once), then the reconstructions; results in examples/tutorial_1/results
docker compose run --rm monalisa python demo/data_demo/data_8_tutorial_1/download_data.py
docker compose run --rm monalisa python examples/tutorial_1/tutorial_1.py \
    --data demo/data_demo/data_8_tutorial_1 --out examples/tutorial_1/results

# tests (xvfb-run: a virtual display for the viewer tests)
docker compose run --rm monalisa xvfb-run -a pytest tests/unit
docker compose run --rm monalisa pytest tests/parity -n auto     # MATLAB recordings in fixtures/matlab

# a Python shell or a terminal
docker compose run --rm monalisa python
docker compose run --rm monalisa bash
```

**Raw data in another folder** (for instance the copy of the MATLAB repository): set
`MONALISA_DATA`, it is mounted where the tutorial expects the data.

```bash
MONALISA_DATA=/path/to/monalisa/demo/data_demo/data_8_tutorial_1 docker compose up
```

## Memory and processors

Tutorial 1 needs about 35 GB of memory (iterative reconstructions of 8 bins of an 80³ image with 42
coils); the gridded reconstructions need much less. The reconstructions use all the processors
the container sees (numba threads); `-e NUMBA_NUM_THREADS=8` limits them.

Measured on a 36-thread Linux computer with Docker Desktop: tutorial 1 in 25 min (22.5 min
outside the container), peak memory 35.8 GB, results identical bit for bit to a run outside the
container.

- **Linux, Docker Engine**: the container uses the computer's memory and processors directly.
- **Docker Desktop** (macOS, Windows, Linux): containers run in a virtual machine whose memory and
  processors are set in *Settings → Resources*; raise the memory above 35 GB for tutorial 1. When
  the limit is reached, the process is stopped with `Killed` (exit code 137).

## Windows: napari viewer and interactive dialogs

In JupyterLab, `show_image` shows images with sliders in the notebook (`view="inline"`, the
default there): this works everywhere, with no display. The napari windows (`"window"`, `"3d"`,
`"ortho"`) and the dialogs of `autoFlag=False` need an X11 display, shared with the container by
[`compose.x11.yaml`](../compose.x11.yaml):

- **Linux with the Docker Engine** (tested on Ubuntu with X11): allow the container's user, then
  start with both compose files:

  ```bash
  xhost +SI:localuser:$(id -un)        # once per session; uid 1000 in the container
  docker compose -f compose.yaml -f compose.x11.yaml up
  ```

  On many desktops `xhost` already lists `SI:localuser:<you>`; then the first line is not needed.
  If your user id is not 1000 (`id -u`), use `xhost +local:` instead. OpenGL is Mesa's software
  renderer: the 3D view of an 80³ volume is fluid, larger volumes are slower.
- **Linux with Docker Desktop**: the virtual machine cannot use the X11 socket of the computer.
  Use the Docker Engine for windows (`docker context use default`, if it is installed), or the
  notebook viewer.
- **Windows 11 (WSL2, WSLg)** and **macOS (XQuartz, `DISPLAY=host.docker.internal:0`)**: the
  same approach can work, but it is not tested; OpenGL through XQuartz is limited, so the 3D view
  may not open. The notebook viewer works.

Without a display, opening a window raises an error that says so; every interactive step also has
a parameter that skips it (README.md, *Viewing images and interactive steps*).

## Published image

The workflow [`.github/workflows/docker.yml`](../.github/workflows/docker.yml) builds the image
and runs the unit tests in it for every change of the `Dockerfile` or of the dependencies, and
publishes it on the GitHub Container Registry when a version tag (`v*`) is pushed. Once published
(and the package made public in the GitHub settings), the image can be used without building it:

```bash
docker pull ghcr.io/mattechlab/monalisa-python:latest
docker run --rm -it -p 127.0.0.1:8888:8888 -v "$PWD":/work ghcr.io/mattechlab/monalisa-python
```

With `-v "$PWD":/work`, the current folder is the working folder in JupyterLab; it should contain
the notebooks and data to work on (for instance a clone of this repository). Without it, the
container works on the copy of the repository in the image, and its changes are lost when it stops.

## Troubleshooting

| Symptom | Cause, fix |
|---|---|
| `Killed`, exit code 137 | not enough memory for the container (Docker Desktop: *Settings → Resources*) |
| files written by the container belong to another user (Linux) | the container runs as uid 1000; with another uid, add `user: "<uid>:<gid>"` to the service in `compose.yaml` |
| `Bind for 127.0.0.1:8888 failed: port is already allocated` | another JupyterLab runs: stop it, or change the first port in `compose.yaml` (`"127.0.0.1:8889:8888"`) |
| `could not connect to display` / `NoDisplayError` | no X11 display shared: `compose.x11.yaml` and `xhost`, see above |
| `libGL error: failed to load driver: ...` when a window opens | harmless: the container has no GPU driver and Mesa renders in software; for hardware rendering on Linux, add `devices: ["/dev/dri:/dev/dri"]` to the service |
| the first reconstruction is slow | numba compiles the kernels on first use and caches them in `src/**/__pycache__` |
