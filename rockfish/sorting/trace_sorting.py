
class SEGYSorting(object):
    """
    Convience class for trace sorting functions.
    """

    def sort_traces(self, *keys, **kwargs):
        """
        In place sorting of SEG-Y traces by trace-header attributes.

        :param traces: List of :class:SEGYTrace objects to sort. 
        :param *keys: List of trace header attributes to use as keys in
            sorting traces. See 
            :const:`obspy.segy.header.TRACE_HEADER_FORMAT` `(source)
  <http://obspy.org/browser/obspy/trunk/obspy.segy/obspy/segy/header.py#L47>`_
            for a list of all available trace header attributes. 

        **kwargs:

        :param reverse: Bool.  If true, traces are sorted in reverse order.
        """
        self._decorate_traces(*keys)
        self.traces.sort()
        return self._undecorate_traces()
            
    def _decorate_traces(self, *keys):
        """
        Decorates traces with trace-header-attribute values.
        """
        dec = []
        for i, tr in enumerate(self.traces):
            _values = []
            for k in keys:
                try:
                    _values.append(tr.header.__getattribute__(k))
                except AttributeError:
                    _values.append(tr.header.__getattr__(k))
            dec.append(_values)
            dec[i].extend([i, tr])
        self.traces = dec
    
    def _undecorate_traces(self):
        """
        Removes trace-header-attribute values from decorated traces.
        """
        self.traces = [d[-1] for d in self.traces]
    

