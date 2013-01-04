"""
Timeshift SEG-Y data.
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
# shift all traces by 1 second
dt_s = np.ones(len(segy1.traces))
# apply shift to the copied data
segy1.timeshift(dt_s, record_delay=False)
# plot original and shifted data
fig = plt.figure()
ax0 = fig.add_subplot(121)
ax1 = fig.add_subplot(122)
splt0 = SEGYPlotter(ax0, segy0)
splt1 = SEGYPlotter(ax1, segy1)
splt0.plot_wiggles(positive_fills=True)
splt1.plot_wiggles(positive_fills=True)
plt.show()

