import numpy as np
import logging
import bitstring as bs

POS0 = {32: 9,
        64: 11}

def sigfigs(values):
    
    return np.asarray([len(str(v)) for v in values]) - 1

def float2bin(values, length=32):

    values = np.atleast_1d(values)
    
    #XXX do we need scaling??
    powers = np.ones(len(values))

    f0 = values / 10. ** powers
    b = np.asarray([bs.BitArray(float=v, length=length).bin\
            for v in f0])

    return b, powers

def bin2float(values, powers):

    values = np.atleast_1d(values)
    powers = np.atleast_1d(powers)
    
    f0 = np.asarray([bs.BitArray(bin=v).float for v in values])
    f0 *= 10. ** powers

    return f0


def crossover(f1, f2, length=64):
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

    b1_0 = [bs.BitArray(float=v, length=length).bin for v in f1]
    b2_0 = [bs.BitArray(float=v, length=length).bin for v in f2]

    f1_1 = np.zeros(f1.shape)
    f2_1 = np.zeros(f2.shape)
    for i, b0 in enumerate(zip(b1_0, b2_0)):
        #ibit = np.random.randint(POS0[length], length)

        #f1_1[i] = bs.BitArray(bin=b0[0][0:POS0[length]]\
        #    + b0[0][POS0[length]: ibit] + b0[1][ibit:]).float
        #f2_1[i] = bs.BitArray(bin=b0[1][0:POS0[length]]\
        #    + b0[1][POS0[length]: ibit] + b0[0][ibit:]).float

        ibit = np.random.randint(0, length)
        f1_1[i] = bs.BitArray(bin=b0[0][0: ibit] + b0[1][ibit:]).float
        f2_1[i] = bs.BitArray(bin=b0[1][0: ibit] + b0[0][ibit:]).float

    if scalar:
        return f1_1[0], f2_1[0]
    else:
        return f1_1.reshape(shape0), f2_1.reshape(shape0)

def mutate(values, length=64, **kwargs):
    """
    Flips all bits in values
    """
    pos = kwargs.get('pos', range(POS0[length], length))


    logging.debug('mutate got type(values) = {:}'.format(type(values)))
    values = np.atleast_1d(values)
    shape0 = values.shape

    logging.debug('...recast as {:} with shape {:}'\
            .format(type(values), shape0))
    
    f0 = values.flatten()

    b = [bs.BitArray(float=_f, length=length) for _f in f0]

    for _b in b:
        _b.invert(pos=pos)

    #[_b.invert(pos=range(length)) for _b in b]

    f1 = np.asarray([_b.float for _b in b])
    

    return f1.reshape(shape0)


