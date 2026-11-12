==============
Hello Monalisa
==============

Hi there, it is your first time here, don't forget to leave us a star if you find this useful.
Our code can be found here : https://github.com/MattechLab/monalisa-python (Python) and
https://github.com/MattechLab/monalisa (MATLAB).

Monalisa is an MRI reconstructions toolbox for 2 or 3 spatial dimensions with 0 or 1 or 2 non-spatial dimensions,
written in Matlab/C++ and ported to Python (this documentation).
You can chose your reconstruction function depending if you want temporal or spatial regularization in the objective functions of the reconstruction problem.
In the case of dynamic imaging, the number of datalines per bin can be different in each bin. We encourage you to write your own reconstructions
by modifying our functions.

In the ``examples`` directory of monalisa-python, we prepared a complete example with data that you can download
as soon as the installation step is done (see next section):

    - The `tutorial 1 notebook <https://github.com/MattechLab/monalisa-python/blob/main/examples/tutorial_1/tutorial_1.ipynb>`_ reconstructs 3D radial brain data step by step: coil sensitivity, binning, mitosius, gridded and iterative reconstructions (see :doc:`3-1_example1`).
    - The same steps as a script: `tutorial_1.py <https://github.com/MattechLab/monalisa-python/blob/main/examples/tutorial_1/tutorial_1.py>`_.
    - The calls of the static reconstructions on a small 2D radial acquisition are in the README, *Example: gridded reconstruction of a 2D radial acquisition*.

Use it to test rapidly our reconstruction framework.
Find in `A mathematical Language for MRI Reconstructions <https://zenodo.org/record/8195815>`_ the mathematics behind our implementations, with references to the literature.

If you are here, you are probably considering our framework for image reconstruction.
Please be aware that you need a coil sensitivity estimation to run our iterative reconstructions. You can estimate the
coil sensitivities either with your own method, or with our method (see documentation). But the second alternative makes use of some
prescan data that you have either to acquire yourself, or that you may found in your raw-data file.
