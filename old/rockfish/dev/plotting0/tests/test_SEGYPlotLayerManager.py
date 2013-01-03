
from rockfish.core.util import get_example_file
from rockfish.segy.segy import readSEGY
from rockfish.plotting.plotsegy import SEGYPlotter
import matplotlib.pyplot as plt


fig = plt.figure()
ax = fig.add_subplot(111)

sgy = readSEGY(get_example_file('ew0210_o30.segy'))
splt = SEGYPlotter()

splt.plot(sgy.traces,negative_fill=True,positive_fill=True,axes=ax,use_manager=True)

splt.manager.toggle('negfills',axes=ax)
splt.manager.toggle('negfills',axes=ax)

plt.show()


