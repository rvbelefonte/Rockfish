# -*- coding: utf-8 -*-

from distutils import sysconfig
from struct import unpack
import ctypes as C
import os
import platform
import logging

# Import shared libsegy depending on the platform.
# create library names
lib_names = [
     # platform specific library name
    'libsegy-%s-%s-py%s' % (platform.system(), platform.architecture()[0],
        ''.join([str(i) for i in platform.python_version_tuple()[:2]])),
     # fallback for pre-packaged libraries
    'libsegy']
# get default file extension for shared objects
lib_extension, = sysconfig.get_config_vars('SO')
# initialize library
clibsegy = None
for lib_name in lib_names:
    try:
        clibsegy = C.CDLL(os.path.join(os.path.dirname(__file__), 'lib',
                                         lib_name + lib_extension))
    except Exception, e:
        pass
    else:
        break
if not clibsegy:
    msg = 'Could not load shared library for obspy.segy.\n\n %s' % (e)
    raise ImportError(msg)


def unpack_header_value(endian, packed_value, length, special_format):
    """
    Unpacks a trace header single value.
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
    logging.debug("Interpreted scalar=%s as %s" %(scalar, fac))

    return fac

def interpret_coordinate_scalar(scalar, units):
    """
    Takes SEG Y trace header scalar attribute and units code and returns the
    corresponding real-valued factor.
    """
    fac = interpret_scalar(scalar)
    if units == 2:
        fac = fac/3.6e3
    logging.debug("Interpreted scalar=%s and coordinate units=%s as %s"
                  %(scalar, units, fac))
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

