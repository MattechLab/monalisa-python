API
===

The public functions and classes of monalisa, by subpackage, generated from their docstrings.
Every one of them is also available from the top-level package: ``monalisa.recon.mathilda`` is
also ``monalisa.mathilda`` (``import monalisa as ml; ml.mathilda(...)``). The arguments keep the
names of the MATLAB functions; :doc:`9-1_renaming` gives the MATLAB name of each function.

.. contents::
   :local:
   :depth: 1

MATLAB names
------------

.. autofunction:: monalisa.find_function

.. data:: monalisa.MATLAB_NAMES

   Dictionary of the ported MATLAB functions: MATLAB name → Python name relative to the package
   (``"bmMathilda"`` → ``"recon.mathilda"``). The table is :doc:`9-1_renaming`.

recon
-----

.. automodule:: monalisa.recon

io
--

.. automodule:: monalisa.io

trajectory
----------

.. automodule:: monalisa.trajectory

geometry
--------

.. automodule:: monalisa.geometry

gridding
--------

.. automodule:: monalisa.gridding

sparse
------

.. automodule:: monalisa.sparse

fourier
-------

.. automodule:: monalisa.fourier

coil
----

.. automodule:: monalisa.coil

binning
-------

.. automodule:: monalisa.binning

image
-----

.. automodule:: monalisa.image

registration
------------

.. automodule:: monalisa.registration

optim
-----

.. automodule:: monalisa.optim

display
-------

.. automodule:: monalisa.display

array
-----

.. automodule:: monalisa.array

util
----

.. automodule:: monalisa.util
