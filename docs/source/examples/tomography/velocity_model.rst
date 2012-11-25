.. _velocity_model:

Build Velocity Models
=====================

A simple, 2D velocity model can be built as follows

.. plot::
     :include-source:

     import numpy as np
     from rockfish.tomography import VM
     vm = VM(r1=(0,0,0), r2=(150, 0, 15), dx=0.5, dz=0.1)
     vm.insert_interface([[z] for z in 1.0 * np.ones((vm.nx))])
     vm.define_constant_layer_velocity(0, 1.5)
     vm.define_stretched_layer_velocities(1, [1.5, 8.0])
     vm.plot()






