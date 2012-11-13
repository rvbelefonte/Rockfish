"""
Routines for working with VM Tomography formats.

Interface Indices
=================

The underlying raytracing and inversion codes are written in
Fortran, and array indices start at ``1``, not ``0`` as in Python.
This discrepency becomes an issue when setting the interface flags
(i.e., ``ir`` and ``ij``). To reconcile this issue, this module
subtracts ``1`` from the ``ir`` and ``ij`` arrays when reading a VM
model from the disk and adds ``1`` to these arrays before writing
a VM model. (In the Python tools, a value of ``-1`` for ``ir`` or
``ij`` is equivalent to a value of ``0`` in the Fortran codes, and
indicates that a node is to be excluded from the inversion.
"""
from vm import VM, readVM
