============
Installation
============

To get started with the MRI reconstruction code, follow these steps. You need Python 3.10 or newer.
There is no C++ compilation step: the MEX files of the MATLAB toolbox are replaced by NumPy, SciPy
and numba code.

.. tip::
   With Docker, nothing has to be installed but Docker: the image ``mattechlab/monalisa-python``
   contains Python, every library, JupyterLab and the tutorial. See :doc:`5_docker`.

Clone the Repository
====================

Clone the repository and navigate into the directory, using your terminal, navigate to the directory where you want to install the monalisa-python folder then run
(on Windows, `Git for Windows <https://git-scm.com/download/win>`_ provides ``git``):

.. code-block:: bash

   git clone https://github.com/MattechLab/monalisa-python.git
   cd monalisa-python

Install the Package
===================

The same commands work on Linux, macOS and Windows. **Either with pip**, in a virtual environment:

.. code-block:: bash

   python3 -m venv .venv                  # Windows: py -m venv .venv
   source .venv/bin/activate              # Windows: .venv\Scripts\activate
   pip install -e ".[io,reg,notebook]"

**or with conda** (everything inside the environment, no admin rights needed):

.. code-block:: bash

   conda create -n monalisa -c conda-forge python=3.12 matplotlib-base
   conda activate monalisa
   pip install -e ".[io,reg,notebook]"

The package installs as ``monalisa-python`` and is imported as ``monalisa``. It always installs
NumPy, SciPy, numba, h5py, matplotlib, napari (viewer and dialogs) and ipywidgets (viewer in
notebooks). The extras add:

- ``io``: the raw-data readers (Siemens ``.dat`` with `twixtools <https://github.com/pehses/twixtools>`_, ISMRMRD ``.mrd`` with ``ismrmrd``);
- ``reg``: SimpleITK, for the deformation fields of motion-compensated reconstructions (it replaces MATLAB's ``imregdemons``);
- ``notebook``: JupyterLab, for the tutorial notebook;
- ``dev``: pytest (with pytest-xdist and pytest-qt), ruff, and ``reg``: ``pip install -e ".[dev,io]"``.

.. warning::
   In a conda environment, install ``matplotlib-base``, not conda's ``matplotlib``: the latter brings
   PySide6 with a second copy of Qt, whose libraries clash with napari's (PyQt6) and crash Python as
   soon as a window opens.

Linux: Library for the Qt Windows
---------------------------------

On Linux only (macOS and Windows need nothing more), the napari viewer and the interactive steps
use Qt, which needs the library libxcb-cursor (not available from pip). Either:

- in the conda environment: ``conda install -c conda-forge xcb-util-cursor`` (monalisa loads it from the environment), or
- system-wide: ``sudo apt install libxcb-cursor0`` (Debian, Ubuntu) or ``sudo dnf install xcb-util-cursor`` (Fedora).

Without it, opening a window raises an error that says so; the notebook viewer works without it.

Verify Installation
===================

Test your installation with the unit tests, and run your first reconstruction with the tutorial (see :doc:`3-1_example1`):

.. code-block:: bash

   python -c "import monalisa; print(monalisa.__version__)"
   pip install -e ".[dev,io]"     # pytest, for the tests
   pytest tests/unit

Congratulations, you are ready to use Monalisa.

Notes
=====

- **Same results as MATLAB**: every ported function is compared with recordings of its MATLAB counterpart (see :doc:`9-2_porting_method`).
- **MATLAB users**: the table :doc:`9-1_renaming` gives the Python name of each MATLAB function; in code, ``monalisa.find_function("bmMathilda")`` returns it.
- **MATLAB files**: ``scipy.io.loadmat`` reads ``.mat`` files saved by MATLAB's default ``save``; ``monalisa.io.loadmat73`` reads ``-v7.3`` files (HDF5) and the files written by this package.

Follow these steps to set up your environment. If you encounter any issues, consider opening an issue on our GitHub repository. We will do our best to help you.
