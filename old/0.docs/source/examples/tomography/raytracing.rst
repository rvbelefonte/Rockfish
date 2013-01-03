.. _raytracing:

Raytracing
==========

Rays can be traced through a velocity model as follows:

.. plot::
     :include-source:

     import numpy as np
     import matplotlib.pyplot as plt
     from rockfish.core.util import get_example_file
     from rockfish.tomography import readVM, readRayfanGroup
     from rockfish.picking.database import PickDatabaseConnection
     from rockfish.tomography.forward import raytrace
      
     vmfile = get_example_file('goc_l26.15.00.vm')
     vm = readVM(vmfile)
     pickdb = PickDatabaseConnection(get_example_file('goc_l26_picks.sqlite'))

     rayfile = 'example.ray'
     raytrace(vmfile, pickdb, rayfile, ensemble=30, vm_branch=3)

     fig = plt.figure()
     ax = fig.add_subplot(111)
     vm.plot(ax=ax, xlim=(20,120), zlim=(20, 0))
     rays = readRayfanGroup(rayfile)
     rays.plot_raypaths(ax=ax)
     plt.show() 
