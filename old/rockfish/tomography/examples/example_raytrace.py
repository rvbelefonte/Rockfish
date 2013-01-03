#!/usr/bin/env python
"""
Raytracing example
==================
"""
import os
import matplotlib.pyplot as plt
from rockfish.picking.database import PickDatabaseConnection
from rockfish.vmtomo.vm import VMFile
from rockfish.vmtomo.rayfan import RayfanFile
from rockfish.vmtomo.raytracing import trace

cleanup = True

# Set filenames for model, pick database, etc.
pickdbfile = 'temp.pickdb.sqlite'
vmfile = '../tests/data/goc_l26.15.00.vm'
#vmfile = '../tests/data/cranis_northeast.00.00.vm'
input_dir = 'temp.input'
rayfile = 'temp.ray'

# Build an example pick database
pickdb = PickDatabaseConnection(pickdbfile)
pickdb.add_pick(event='Pg', ensemble=100, trace=1,
        vm_branch=3, vm_subid=0,
        time=5.0, time_reduced=5.0,
        source_x=50, source_y=0.0, source_z=0.006,
        receiver_x=100, receiver_y=0.0, receiver_z=2)
pickdb.commit()

# Raytrace the model
trace(vmfile, pickdb, rayfile, input_dir=input_dir, cleanup=False) 

# Plot model and rays
fig = plt.figure()
ax = fig.add_subplot(311)
vm = VMFile(vmfile)
vm.plot(ax=ax)
ax.set_aspect(2)
plt.xlim((vm.r1[0], vm.r2[0]))
plt.ylim((vm.r2[2], vm.r1[2]))

if os.path.isfile(rayfile):
    rays = RayfanFile(rayfile)
    for rfn in rays.rayfans:
        for path in rfn.paths:
            x = [p[0] for p in path]
            z = [p[2] for p in path]
            ax.plot(x, z, color='0.75')

inst = pickdb.get_ensembles()
for _inst in inst:
    x,y,z = pickdb.get_vmtomo_instrument_position(_inst)
    ax.plot(x,z,'vy')

plt.show()

# Clean up example files
if cleanup:
    for filename in [pickdbfile,input_dir, rayfile]:
        if os.path.isfile(filename):
            os.remove(filename)
