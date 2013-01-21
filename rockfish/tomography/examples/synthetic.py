#!/usr/bin/env python
"""
Example showing how to use the Rockfish interface to the VM Tomography
programs.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from rockfish.tomography import VM, readVM, readRayfanGroup
from rockfish.picking.database import PickDatabaseConnection
from rockfish.tomography.forward import raytrace
from rockfish.tomography.rayfan import rayfan2db

# Filenames
vmfile = 'synthetic.vm'
temp_pickdb_file = 'temp.sqlite'
rayfile = 'synthetic.ray'
pickdb_file = 'synthetic.sqlite'

# Cleanup from any earlier run
for filename in [vmfile, temp_pickdb_file, rayfile, pickdb_file]:
    if os.path.isfile(filename):
        os.remove(filename)

# Create a simple 1D model
vm = VM(r1=(0, 0, 0), r2=(100, 0, 15), dx=0.5, dy=1, dz=0.1)
vm.insert_interface(np.asarray([[z] for z in 2.0 * np.ones((vm.nx))]))
vm.define_constant_layer_velocity(0, 1.5)
vm.define_stretched_layer_velocities(1, [1.5, 4.0, 6.5, 8.0, 8.5])
vm.write(vmfile)

# Create a pickdb to define source/receiver geometry
pickdb = PickDatabaseConnection(temp_pickdb_file)
sx = np.arange(1., 80., 1.)
rx = [1.]
for irec, _rx in enumerate(rx):
    for isrc, _sx in enumerate(sx):
        d = {'event': 'Pg',
             'vm_branch': 1,
             'vm_subid': 0,
             'ensemble': irec + 10,
             'trace': isrc + 5000,
             'time': 0.0,
             'time_reduced': 0.0,
             'source_x': _sx,
             'source_y': 0.0,
             'source_z': 1.0,
             'receiver_x': _rx,
             'receiver_y': 0.0,
             'receiver_z': 2.0,
             'offset' : np.abs(_rx - _sx)}
        pickdb.update_pick(**d)
    pickdb.commit()

# Raytrace with these picks
raytrace(vmfile, pickdb, rayfile)
pickdb.close()

# Transfer traced to a picks to a new pick database and add noise
pickdb = rayfan2db(rayfile, pickdb_file, synthetic=True, noise=0.02)

# Raytrace with the new pick database
raytrace(vmfile, pickdb, rayfile)

# Plot the traced rays and traveltimes
fig = plt.figure()
ax = fig.add_subplot(211)
vm.plot(ax=ax)
rays = readRayfanGroup(rayfile)
rays.plot_raypaths(ax=ax)
ax = fig.add_subplot(212)
rays.plot_time_vs_position(ax=ax)
ax.set_xlim([vm.r1[0], vm.r2[0]])
plt.show()

