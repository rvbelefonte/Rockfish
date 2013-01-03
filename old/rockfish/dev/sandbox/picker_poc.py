# Proof of concept for a Python-only interactive seismic data picker.

import numpy as np
import matplotlib.pyplot as plt
from obspy.segy.segy import readSEGY


def wiggle(traces,limits,pencolor='black'):
    """
    Add trace wiggles for data in the SEGYFile object `segy` into
    the matplotlib axes `ax`.
    """

    # init the plot
    ax_lims = limits
    ax_lims[0] = limits[0] - 1
    ax_lims[1] = limits[1] + 1
    plt.axis(ax_lims)


    # Load amplitude data into an array for easy indexing
    amp = traces2array(traces)
    amp_max = np.max(abs(amp.view()))*2

    dx = 1
    gain = 1

    # plot data
    for i in range(limits[0],limits[1]):
        xplt = (i + 1) * dx

        tr = traces[i]
        dt_s = tr.header.sample_interval_in_ms_for_this_trace/1.e6
        time = np.asarray(range(0,tr.npts))*dt_s
        amp_max = max(amp[i])*2

        plot_wiggle_trace(time,amp[i],xplt=xplt,amp_max=amp_max,gain=gain)


    return fig, ax

def plot_wiggle_trace(time,amp,pencolor='black',amp_max=1,gain=1,xplt=0,penwidth=0.5):


    trace = xplt + np.array(amp)*gain/amp_max

    ax.plot(trace,time,color=pencolor,linewidth=penwidth)


    return



def traces2array(traces):
    """
    Load data from the SEGYFile object `segy` into a `numpy.array` object.
    """

    d = []
    for i in range(0,len(traces)):
        d.append(traces[i].data)

    return np.array(d)


def onclick(event):
    #print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
    #    event.button, event.x, event.y, event.xdata, event.ydata)
    
    gain = 1
    dx = 1
    ix = int(round(event.xdata)) - 1
    xplt = (ix + 1) * dx
    tr = segy.traces[ix]
    dt_s = tr.header.sample_interval_in_ms_for_this_trace/1.e6
    time = np.asarray(range(0,tr.npts))*dt_s
    amp = segy.traces[ix].data
    t_pick = event.ydata
    amp_pick = np.interp(event.ydata,time,amp)
    amp_max = max(amp)*2

    trace_pick = xplt + amp_pick*gain/amp_max

    
    plot_wiggle_trace(time,amp,xplt=xplt,amp_max=amp_max,gain=gain,pencolor='green')

    print 'button=%d, ix=%i, t=%d, amp=%f'%(
        event.button, ix, t_pick, amp_pick)

    ax.plot(event.xdata,event.ydata,'+r')
    ax.plot(trace_pick,t_pick,'.r')
    fig.canvas.draw()

    return

filename = '../tests/data/obs.segy' 
    
segy = readSEGY(filename,unpack_headers=True)

nplt = 10

fig = plt.figure()
ax = fig.add_subplot(111)


wiggle(segy.traces,[0,nplt-1,0,8])

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()



