"""
Time shift for SEG-Y data.
"""
import numpy as np

class SEGYTimeshifts(object):
    """
    Functions for time-shifting SEG-Y data.
    """

    def timeshift(self, dts, traces=None, record_delay=False):
        """
        Timeshift data by phase shifting in the frequency domain.

        :param dts: List of the values for the timeshift in seconds 
            for each trace.
        :param traces: Optional. List of ``SEGYTrace`` objects with data to
            timeshift.  Default is to shift all traces.
        :param record_delay: Optional. Determines whether or not to add the
            timeshift to the existing trace header delay time attribute. 
            Default is False.
        """
        if traces is None:
            traces = self.traces
        if len(dts) != len(traces):
            msg = 'Length of dtimes must equal number of traces. '\
                + '(len(dts) = %i, but len(traces) = %i.)'\
                    %(len(dts), len(traces))
            raise ValueError(msg)
        for i,tr in enumerate(traces):
            dt_sec = tr.header.sample_interval_in_ms_for_this_trace/1.e6
            f = np.fft.fftfreq(len(tr.data))
            F = np.fft.fft(tr.data) * np.exp(-2j*np.pi*f*dts[i]/dt_sec)
            # XXX casting as 32-bit here so we can write!
            # XXX need a more general way to handle this!
            tr.data = np.float32(np.real(np.fft.ifft(F)))
            if record_delay:
                tr.header.delay_recording_time_in_ms += -dts[i]*1000.

    def apply_velocity_reduction(self, reduction_velocity, 
            current_reduction_velocity=None, data_length=None, traces=None,
            record_delay=True):
        """
        Shift trace data in time by dt = time - offset/reduction_velocity.
        
        :param reduction_velocity: Reduction velocity in km/s.  If set to
            ``None``, reduction at the ``current_reduction_velocity`` will be 
            removed.
        :param current_reduction_velocity: Optional. Current reduction velocity
            in km/s. Default is to assume that the data are unreduced 
            (``current_reduction_velocity=None``).
        :param data_length: Optional. Length of data in seconds to keep after
            reduction. Default is to keep all data.
        :param traces: Optional. List of ``SEGYTrace`` objects with data to
            reduce.  Default is to reduce all traces.
        :param record_delay: Optional. Determines whether or not to add the
            velocity reduction timeshift to the existing trace header delay
            time attribute. Default is True.
        """
        if traces is None:
            traces = self.traces
        # Calculate timeshifts for all traces
        dts = []
        for tr in traces:
            x_km = abs(tr.header.source_receiver_offset_in_m) * 0.001
            dts.append(0)
            if reduction_velocity is not None:
                dts[-1] += -x_km/reduction_velocity
            if current_reduction_velocity is not None:
                dts[-1] += x_km/current_reduction_velocity
        # Apply timeshifts
        self.timeshift(dts, traces, record_delay=record_delay)
        # Throw out extra data
        if data_length is not None:
            for tr in traces:
                npts = data_length\
                        /tr.header.sample_interval_in_ms_for_this_trace
                tr.data = tr.data[0:npts]
                tr.header.number_of_samples_in_this_trace = npts
