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
from rockfish.tomography.rayfan import rayfan2pickdb

# Create a simple 1D model
vmfile = 'synthetic.vm'
vm = VM(r1=(0, 0, 0), r2=(100, 0, 15), dx=0.5, dy=1, dz=0.1)
vm.insert_interface([[z] for z in 1.0 * np.ones((vm.nx))])
vm.define_constant_layer_velocity(0, 1.5)
vm.define_stretched_layer_velocities(1, [4.0, 4.0, 6.5, 7.2, 8.0])
vm.write(vmfile)

# Create a pickdb to define source/receiver geometry
temp_pickdb_file = 'temp.sqlite'
if os.path.isfile(temp_pickdb_file):
    os.remove(temp_pickdb_file)
pickdb = PickDatabaseConnection(temp_pickdb_file)
sx = np.arange(40., 60., 1.)
rx = [10., 20., 30.]
for irec, _rx in enumerate(rx):
    for isrc, _sx in enumerate(sx):
        d = {'event': 'Pg',
             'vm_branch': 1,
             'vm_subid': 0,
             'ensemble': irec,
             'trace': isrc,
             'time': 0.0,
             'time_reduced': 0.0,
             'source_x': _sx,
             'source_y': 0.0,
             'source_z': 0.006,
             'receiver_x': _rx,
             'receiver_y': 0.0,
             'receiver_z': 0.90}
        pickdb.update_pick(**d)
    pickdb.commit()

# Raytrace with these picks
rayfile = 'synthetic.ray'
raytrace(vmfile, pickdb, rayfile)
pickdb.close()
#os.remove(temp_pickdb_file)

# Transfer traced to a picks to a new pick database and add noise
pickdb_file = 'synthetic.sqlite'
pickdb = rayfan2pickdb(rayfile, pickdb_file, mode='traced', noise=0.02)

# Raytrace with the new pick database
#raytrace(vmfile, pickdb, rayfile)

# Plot the traced rays
fig = plt.figure()
ax = fig.add_subplot(211)
vm.plot(ax=ax, rf=False)
rays = readRayfanGroup(rayfile)
rays.plot_raypaths(ax=ax)
ax = fig.add_subplot(212)
rays.plot_traveltimes(ax=ax)
plt.xlim((vm.r1[0], vm.r2[0]))
plt.show()
