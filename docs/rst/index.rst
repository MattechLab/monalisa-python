.. Monalisa (Python) documentation master file. Same structure as the documentation of the
   MATLAB toolbox (https://mattechlab.github.io/monalisa/), with the code in Python.

=============================================
Welcome to Monalisa's documentation (Python)!
=============================================

.. note::
   This is the documentation of **monalisa-python**, the Python port of the
   `Monalisa <https://github.com/MattechLab/monalisa>`_ MATLAB toolbox
   (`its documentation <https://mattechlab.github.io/monalisa/>`_). The explanations are the same;
   the code is Python. Every ported function keeps the arguments and array conventions of its
   MATLAB counterpart, under a Python name (``bmMathilda`` → ``monalisa.mathilda``):
   see :doc:`9-1_renaming`.

First of all, why should you use Monalisa?

1. **Monalisa targets non-Cartesian reconstructions, motion-resolved/motion-corrected reconstructions, and partial Cartesian reconstructions.**
   It offers great tools especially for radial imaging and motion-resolved/motion-corrected reconstructions. These are the best use cases for the current toolbox.

2. **Monalisa is easy to install and well documented** – as you can see!

3. **Monalisa is great for learning non-Cartesian iterative reconstruction methods.**


.. image:: ../images/monalisaworkflow.png
   :width: 100 %

Here you can see a simplified schematic of the pipeline in Monalisa. Information from the acquisition raw data files is processed through multiple stages, together with additional information, such as the trajectory, volume elements, and user-defined binning and reconstruction parameters. Colored blocks indicate the degree of user control: red denotes acquisition-specific steps that are fixed and cannot be modified after acquisition; yellow highlights configurable steps that are rarely changed but can be customized or improved; green represents user-defined steps that must be adapted for each reconstruction. Initially, the workflow defines binning masks alongside coil sensitivity estimation and volume element computation. This is followed by the mitosius preparation, and finally, image reconstruction. The sections below are explaining each step extensively. Need more help? Consider opening a GitHub issue on our repository.

.. toctree::
   :maxdepth: 3
   :glob:
   :includehidden:

   1_quick_start
   2_contents
   3_examples

.. toctree::
   :maxdepth: 1
   :glob:
   :includehidden:

   4_api

.. toctree::
   :maxdepth: 3
   :glob:
   :includehidden:

   5_docker
   6_ack_contribution

.. toctree::
   :maxdepth: 2
   :includehidden:

   9_python_port
