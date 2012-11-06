"""
Functions for the genetic algorithm.
"""
from BitVector import BitVector
from struct import pack, unpack

ENDIAN = '>'


def float2bitvec(floatval):
    """
    Convert a Python float to IEEE floating point bits.

    :based on: http://vislab-ccom.unh.edu/~schwehr/ais/waterlevel/downloads/html/ais.binary-module.html#float2bitvec

    :param floatval: Float value to convert.
    :returns: Binary bit vector

    >>> print float2bitvec(1.)
    00111111100000000000000000000000
    
    >>> print float2bitvec(-1.)
    10111111100000000000000000000000
    """
    s = pack('{:}f'.format(ENDIAN),floatval)
    i = unpack('{:}I'.format(ENDIAN),s)[0]
    bvList = []
    for i in range(4):
        bv1 = set_bitvector_size(BitVector(intVal=ord(s[i])),8)
        bvList.append(bv1)
    return join_bitvector(bvList)

def bitvec2float(bv):
    """
    Convert a bit vector to a Python float.

    :param bv: BitVector instance
    :returns: float value

    >>> print bitvec2float(float2bitvec(1.))
    1.0
    
    >>> print bitvec2float(float2bitvec(-1.))
    -1.0

    """
    return unpack('{:}f'.format(ENDIAN),chr(bv[0:8]) + chr(bv[8:16])\
                  + chr(bv[16:24]) + chr(bv[24:32]))[0]

def set_bitvector_size(bv,size=8): 
    """
    Pad a BitVector with 0's on the left until it is at least the size 
    specified 

    :param bv: BitVector that needs to meet a minimim size 
    :type bv: BitVector 
    :param size: Minimum number of bits to make the new BitVector 
    :type size: int 
    :returns: BitVector that is size bits or larger 
    :rtype: BitVector 

    """ 
    pad = BitVector(bitlist=[0]) 
    while len(bv)<size: bv = pad + bv 
    return bv 

def join_bitvector(bvSeq): 
    """ 
    Combine a sequence of bit vectors into one large BitVector 
    :param bvSeq: sequence of bitvectors 
    :return: aggregated BitVector 
    :bug: replace with a faster algorithm! 
    """ 
    bvTotal=BitVector(size=0) 
    for bv in bvSeq: 
        bvTotal = bvTotal + bv 
    return bvTotal

if __name__ == "__main__":
    import doctest
    doctest.testmod()
