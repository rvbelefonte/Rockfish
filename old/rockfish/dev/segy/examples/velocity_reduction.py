"""
Apply a velocity reduction to SEG-Y data.
"""

from rockfish.segy.segy import readSEGY, SEGYFile
from rockfish.core.util import get_example_file
from rockfish.plotting.plotters import SEGYPlotter
import matplotlib.pyplot as plt
import numpy as np

# Read SEG-Y data
segy0 = readSEGY(get_example_file('ew0210_o30.segy'))
# Make a copy
segy1 = SEGYFile(segy0)
# Reduce the data at 8 km/s
segy1.apply_velocity_reduction(None, 7., record_delay=False)
segy1.apply_velocity_reduction(7., None, record_delay=True)
# plot original and shifted data
fig = plt.figure()
ax0 = fig.add_subplot(121)
ax1 = fig.add_subplot(122)
splt0 = SEGYPlotter(ax0, segy0)
splt1 = SEGYPlotter(ax1, segy1)
splt0.plot_wiggles(positive_fills=True)
splt1.plot_wiggles(positive_fills=True)
plt.show()

