from rockfish.core.util import get_example_file
from rockfish.segy.segy import readSEGY
from rockfish.plotting.plotsegy import SEGYPlotter
from rockfish.picking.picksegy import SEGYPickDatabase
import matplotlib.pyplot as plt


fig = plt.figure()
ax = fig.add_subplot(111)

sgy = readSEGY(get_example_file('ew0210_o30.segy'))
splt = SEGYPlotter()
pickdb = SEGYPickDatabase('/Users/ncm/Desktop/obs.sqlite')

splt.plot(sgy.traces,negative_fill=True,positive_fill=True,axes=ax,
          pickdb=pickdb,picks=True,
          use_manager=True)

plt.show()
