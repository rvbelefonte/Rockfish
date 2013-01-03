"""
Utility functions.
"""
from obspy.segy.segy import SEGYError

class SEGYUtils(object):
    """
    Utility functions for working with :class:`SEGYFile` objects.
    """
    def traces2grid(self):
        """
        Creates a grid of data from trace data.

        .. warning:: Assumes that traces are all of a uniform length.
        
        :param traces: Optional. List of :class:`SEGYTrace` objects with data 
            to include in the array. Default is to include data from all 
            traces.
        :returns: 2D numpy array of data
        """
        if traces is None:
            traces = self.traces
        ntrc = len(self.traces)
        ntime = len(self.traces[0].data)
        data = np.empty([ntrc,ntime])
        for i,tr in enumerate(self.traces):
            data[i] = tr.data
        return data

    def grid2traces(self, data, traces=None):
        """
        Copies data from a grid to traces.
        
        :param data: ntrace x ndata array of data to transfer to traces. 
        :param traces: Optional.  List of :class:`SEGYTrace` objects to 
            transfer data to.  Default is to copy data to all traces.
        """
        if traces is None:
            traces = self.traces
        if len(data) != len(traces):
            msg = 'Number of rows in data must match number of traces. '\
                + '(len(data) = %i, but len(traces) = %i.)'\
                    %(len(data), len(traces))
            raise ValueError(msg)
        for i,tr in enumerate(self.traces):
            if len(self.traces[i].data) != len(data[i]):
                self.traces[i].header.number_of_samples_in_this_trace = \
                    len(data[i])
            self.traces[i].data = data[i]

def calc_reduction_time(reduction_velocity, offset, 
                        current_reduction_velocity=None):
    """
    Calculate timeshift for velocity reduction at a given offset.
    """
    dt = 0
    if reduction_velocity is not None:
        dt += -abs(offset)/reduction_velocity
    if current_reduction_velocity is not None:
        dt += abs(offset)/current_reduction_velocity
    return dt
