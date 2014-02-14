import numpy as np
import logging
import bitstring

def float2bin(values, length=32):

    values = np.atleast_1d(values)

    return np.asarray([bitstring.BitArray(float=v, length=length).bin\
            for v in values])

def bin2float(values):

    values = np.atleast_1d(values)
    
    return np.asarray([bitstring.BitArray(bin=v).float for v in values])


def crossover(f1, f2, nbits=32):
    """
    binary crossover of two floating point numbers or values in arrays
    """
    if hasattr(f1, '__iter__'):
        scalar = False
    else:
        scalar = True

    f1 = np.atleast_1d(f1)
    f2 = np.atleast_1d(f2)

    shape0 = f1.shape
    assert f1.shape == f2.shape, 'f1.shape must be equal to f2.shape'

    f1 = f1.flatten()
    f2 = f2.flatten()

    b1_0 = float2bin(f1, length=nbits)
    b2_0 = float2bin(f2, length=nbits)

    f1_1 = np.empty(f1.shape)
    f2_1 = np.empty(f2.shape)
    for i, b0 in enumerate(zip(b1_0, b2_0)):
        ibit = np.random.randint(0, nbits)

        f1_1[i] = bin2float(b0[0][0: ibit] + b0[1][ibit:])
        f2_1[i] = bin2float(b0[1][0: ibit] + b0[0][ibit:])

    if scalar:
        return f1_1[0], f2_1[0]
    else:
        return f1_1.reshape(shape0), f2_1.reshape(shape0)

def mutate(values, length=32, nan=0.):
    """
    Flips all bits in values
    """
    logging.debug('mutate got type(values) = {:}'.format(type(values)))
    values = np.atleast_1d(values)
    shape0 = values.shape

    logging.debug('...recast as {:} with shape {:}'\
            .format(type(values), shape0))
    
    f0 = values.flatten()

    b = float2bin(f0, length=length)
    b1 = [''.join([str(abs(int(v) - 1)) for v in _b]) for _b in b]

    f1 = bin2float(b1)

    idx = np.isnan(f1)
    f1[idx] = f0[idx]
    
    return f1.reshape(shape0)


