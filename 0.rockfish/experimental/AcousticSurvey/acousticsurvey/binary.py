"""
Binary operations on floating point numbers.
"""
from ast import literal_eval
import numpy as np

def float2bin(val):
    """
    Convert a Python float to a bit vector.

    :param val: Float value to convert.
    :returns: bit vector, power of 10, sign
    """
    sign = np.sign(val)
    val = np.abs(val)
    pow10 = len(str(val).split('.')[1])
    bv = [int(v) for v in bin(int(val*10**pow10))[2:]]
    return bv, pow10, sign

def bin2float(bv, pow10, sign=1):
    """
    Convert the output of float2bin back to a float.

    :param bv: Bit vector
    :param pow10: power of 10 of the number represented by ``bv``
    :param sign: Optional. Sign of the value. Default is positive.
    :returns: floating point value
    """
    return sign*literal_eval('0b' + ''.join([str(v) for v in bv]))\
            *10**-pow10

def mutate(val):
    """
    Binary mutation of a floating point value.
    
    .. warning:: Values will not change sign.

    :param val: Value to mutate
    :returns: Mutated floating point value
    """
    bv, pow10, sign = float2bin(val)
    irank = int(np.random.rand()*len(bv)-1)
    bv = bv[0:irank] + list(np.abs(np.asarray(bv[irank:])-1))
    return bin2float(bv, pow10, sign)

def crossover(val1, val2):
    """
    Binary crossover of two values.

    Values to crossover are selected at random.

    .. warning:: Output value will have the same order of magnitude 
        and sign as ``val1``.

    :param val1, val2: Values to cross.
    :returns: Crossed value.
    """
    # Convert floats to bit vectors
    bv1, pow10_1, sign1 = float2bin(val1)
    bv2, pow10_2, sign2 = float2bin(val2)
    # Pad smaller value with zeros
    ndigit = max(len(bv1), len(bv2))
    bv1 = [0 for i in range(0, ndigit-len(bv1))] + bv1
    bv2 = [0 for i in range(0, ndigit-len(bv2))] + bv2
    # Crossover all numbers with rank less than a randomly 
    # selected rank
    irank = int(np.random.rand()*ndigit-1)
    bvx = bv1[0:irank] + bv2[irank:]
    return bin2float(bvx, pow10_1, sign1)
