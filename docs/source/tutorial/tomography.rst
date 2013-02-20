
.. _tomography-tutorial:

Tomography
**********

Rockfish includes a set of tools and wrappers to make using an academic 
travel-time tomography code known as "VM Tomography" a bit more
streamlined.  The following examples show how to use some of these tools.

Ensure that VM programs are in your path
========================================

The wrappers in :mod:`rockfish.tomography` call these programs:

**slim_rays** -- *Raytracing program*

**vm_tomo** -- *Tomographic inversion program*

**vm_smooth_model** -- *Program that performs smoothing of tomography results*

Before running the examples below, verify that these programs are in your path:

.. code-block:: bash

     which slim_rays
     which vm_tomo
     which vm_smooth_model

Create a simple velocity model
==============================

A new velocity model can be created like this:

.. plot::
     :include-source:

     >>> import numpy as np
     >>> from rockfish.tomography import VM
     >>> r1 = (0, 0, 0)  # xmin, ymin, zmin
     >>> r2 = (100, 0, 15)  # xmax, ymax, zmax
     >>> vm = VM(r1=r1, r2=r2, dx=0.5, dy=1, dz=0.1)
     >>> vm.insert_interface(np.asarray([[z] for z in 2.0 * np.ones((vm.nx))]))
     >>> vm.define_constant_layer_velocity(0, 1.5)
     >>> vm.define_stretched_layer_velocities(1, [1.5, 4.0, 6.5, 8.0, 8.5])
     >>> vm.plot()

To write this model to the disk in the native VM Tomography binary format,
use:

>>> vm.write('/path/to/model.vm')

This model can be read back from the disk using:

>>> from rockfish.tomography import readVM
>>> vm = readVM('/path/to/model.vm')

Raytrace a model
================

Rockfish can handle raytracing of VM models using travel times stored in
its own :class:`rockfish.picking.database.PickDatabaseConnection` database
structure.  (See the :ref:`pick database tutorial <pickdatabase-tutorial>` to learn about creating a database.)

An existing model can be raytraced and plotted like this:

.. plot::
     :include-source:

     >>> from rockfish.utils.loaders import get_example_file
     >>> from rockfish.picking.database import PickDatabaseConnection
     >>> from rockfish.tomography import readVM, readRayfanGroup, raytrace, VMPlotter
     >>> vmfile = get_example_file('goc_l26.15.00.vm')
     >>> vm = readVM(vmfile)
     >>> pickdb = PickDatabaseConnection(get_example_file('goc_shot_gather.sqlite'))
     >>> rayfile = 'example.rays'
     >>> raytrace(vmfile, pickdb, rayfile)
     >>> rays = readRayfanGroup(rayfile)
     >>> vplt = VMPlotter(vm, rays)
     >>> vplt.plot2d()
