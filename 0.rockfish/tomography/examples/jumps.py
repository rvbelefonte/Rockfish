#!/usr/bin/env python
"""
Demonstrate the effect of slowness jumps on the velocity grid.
"""
import numpy as np
from mpl_toolkits.axes_grid import Divider
import matplotlib.pyplot as plt
from rockfish.tomography import VM


# Initialize a new model
vm = VM(r1=(0, 0, 0), r2=(50, 0, 30), dx=0.5, dy=0.5, dz=0.5)

# Create a background velocity gradient across the entire grid
vm.define_constant_layer_gradient(0, 0.1, v0=1.5)


# Add a few layers
for z in [5, 10, 20]:
    vm.insert_interface(z * np.ones((vm.nx, vm.ny)))

# Add slowness jumps on specific interaces
vm.jp[0] -= 0.01
vm.jp[1] -= 0.02
vm.jp[2] -= 0.03

# Plot smooth model
fig = plt.figure()
ax = fig.add_subplot(131)
vm.plot(ax=ax, apply_jumps=False, vmin=1.5, vmax=5)
plt.title('Smooth Velocities')
plt.xlabel('x-offset (km)')
plt.ylabel('Depth (km)')

# Plot jumped model
ax = fig.add_subplot(132)
vm.plot(ax=ax, apply_jumps=True, vmin=1.5, vmax=5)
plt.title('Jumped Velocities')
plt.xlabel('x-offset (km)')
plt.ylabel('Depth (km)')

# Plot velocity-depth profiles after applying jumps sucessively
ax = fig.add_subplot(133)
vm.plot_profile(ax=ax, x=25, y=0, apply_jumps=False)
plt.title('Velocity Profiles')
plt.xlabel('Velocity (km/s)')
plt.ylabel('Depth (km)')
for iref in range(0, vm.nr):
    vm.apply_jumps(iref=[iref])
    vm.plot_profile(ax=ax, x=25, y=0, apply_jumps=False)
    ax.set_ylim(ax.get_ylim()[::-1])
plt.show()

# Write out model
vm.write('jump1d.vm')

