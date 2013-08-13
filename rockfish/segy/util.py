# -*- coding: utf-8 -*-
"""
Utility functions and classes.
"""
from struct import unpack
import os


def unpack_header_value(endian, packed_value, length, special_format):
    """
    Unpacks a single value.
    """
    # Use special format if necessary.
    if special_format:
        format = '%s%s' % (endian, special_format)
        return unpack(format, packed_value)[0]
    # Unpack according to different lengths.
    elif length == 2:
        format = '%sh' % endian
        return unpack(format, packed_value)[0]
    # Update: Seems to be correct. Two's complement integers seem to be
    # the common way to store integer values.
    elif length == 4:
        format = '%si' % endian
        return unpack(format, packed_value)[0]
    # The unassigned field. Since it is unclear how this field is
    # encoded it will just be stored as a string.
    elif length == 8:
        return packed_value
    # Should not happen
    else:
        raise Exception

# Functions for converting SEG-Y trace header coordinates and elevations from
# signed integers to real values according to the SEG-Y format.
def interpret_scalar(scalar):
    """
    Takes a SEG Y trace header scalar attribute and returns the corresponding
    real-valued factor.
    """
    if(scalar < 0):
        fac = 1./float(abs(scalar))
    elif(scalar > 0):
        fac = float(abs(scalar))
    else:
        fac = float(1)
    return fac

def interpret_coordinate_scalar(scalar, units):
    """
    Takes SEG Y trace header scalar attribute and units code and returns the
    corresponding real-valued factor.
    """
    fac = interpret_scalar(scalar)
    if units == 2:
        fac = fac/3.6e3
    return fac

def get_scaled_coordinate(header, attribute):
    """
    Scale trace header coordinate attributes according to unit and scalar
    attributes.
    """
    # Get units and scalar from header
    scalar = interpret_coordinate_scalar(
        header.scalar_to_be_applied_to_all_coordinates,
        header.coordinate_units)
    # get unscaled integer
    try:
        value = header.__getattribute__(attribute)
    except AttributeError:
        value = header.__getattr__(attribute)
    # apply scalar 
    return float(value)*scalar

def set_unscaled_coordinate(header, attribute, value):
    """
    Unscale trace header coordinate value and set it.
    """
    # Get units and scalar from header
    scalar = 1./interpret_coordinate_scalar(
        header.scalar_to_be_applied_to_all_coordinates,
        header.coordinate_units)
    # Scale real value to integer value
    header.__setattr__(attribute, int(value*scalar))

def get_scaled_elevation(header, attribute):
    """
    Scale trace header elevation attributes according to header elevation scalar
    attribute.
    """
    # get scalar from the header
    scalar = interpret_scalar(
        header.scalar_to_be_applied_to_all_elevations_and_depths)
    # get unscaled integer
    try:
        value = header.__getattribute__(attribute)
    except AttributeError:
        value = header.__getattr__(attribute)
    # apply scalar 
    return float(value)*scalar

def set_unscaled_elevation(header, attribute, value):
    """
    Unscale an elevation and set its header value.
    """
    # get scalar from the header
    scalar = interpret_scalar(
        header.scalar_to_be_applied_to_all_elevations_and_depths)
    # Scale real value to integer value 
    header.__setattr__(attribute, int(value*scalar))


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
