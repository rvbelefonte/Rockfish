"""
Utilities for working with bits
"""
import numpy as np
import copy
import logging
from functools import partial
from bitstring import BitArray

#XXX Dev
#logging.basicConfig(level='DEBUG')

POS0 = {32: 9,
        64: 12}

class BitList(list):

    def __init__(self, values, *args, **kwargs):

        self.LENGTH = kwargs.pop('length', 64)

        assert self.LENGTH in [32, 64], 'length must be 32 or 64'

        values = np.atleast_1d(values).flatten()

        if self.LENGTH == 64:
            dtype = np.float64
        else:
            dtype = np.float32

        for v in values:
            self.append(BitArray(float=dtype(v), length=self.LENGTH))

    def _get_bin(self):
        return [_b.bin for _b in self]
    bin = property(fget=_get_bin)
    
    def _get_float(self):
        return [_b.float for _b in self]
    float = property(fget=_get_float)

    def bitarray_method(self, name, *args, **kwargs):
        for b in self:
            b.__getattribute__(name)(*args, **kwargs)

    def invert(self, pos=None):
        self.bitarray_method('invert', pos=pos)

    def invert_rand(self):
        pos = np.random.randint(0, self.LENGTH, 
                np.random.randint(0,  self.LENGTH, 1))
        self.invert(pos=pos)

    def invert_significant(self, pos=None, sign=True):

        if pos is None:
            pos = range(POS0[self.LENGTH],  self.LENGTH)

        if sign:
            pos = pos + [0]

        self.invert(pos=pos)

    def invert_rand_significant(self, sign=True):

        imax = self.LENGTH - POS0[self.LENGTH] + 1
        pos = np.random.randint(POS0[self.LENGTH], self.LENGTH,
                np.random.randint(0, imax, 1))
        if sign:
            isign = np.random.randint(0, 2)
            if isign:
                pos = [0] + list(pos)

        self.invert(pos=pos)

    def crossover(self):
    
        idx = range(len(self))
        for i in idx:
            for j in idx:
                b0 = self[i].bin
                b1 = self[j].bin

                ibit = np.random.randint(0, self.LENGTH)

                self[i] = BitArray(bin=b0[0: ibit] + b1[ibit:])
                self[j] = BitArray(bin=b1[0: ibit] + b0[ibit:])

    def crossover_significant(self, i1, i2):

        ibit0 = POS0[self.LENGTH]
    
        b0 = self[i1].bin
        b1 = self[i2].bin

        ibit = np.random.randint(POS0[self.LENGTH], self.LENGTH)

        self[i1] = BitArray(bin=b0[0:ibit0] + b0[ibit0: ibit]\
                + b1[ibit:])
        self[i2] = BitArray(bin=b1[0:ibit0] + b1[ibit0: ibit]\
                + b0[ibit:])


class BitSet(object):

    def __init__(self, values, nbits=64, inplace=True):

        values = np.atleast_1d(values)

        self.inplace = inplace
        self.size = values.size
        self.shape = values.shape
        self.nbits = nbits

        values = values.flatten()

        if self.nbits == 64:
            self.dtype = np.float64
        else:
            self.dtype = np.float32

        self._bitarray = [BitArray(float=self.dtype(v), length=self.nbits)\
                for v in values]

    # Inplace vs. copying
    def _inplace(self, **kwargs):
        inplace = kwargs.pop('inplace', self.inplace)
        if inplace:
            bs = self
        else:
            bs = copy.deepcopy(self)

        return bs

    # Array and matrix indexing
    def _get_flat_idx(self):
        return np.arange(0, self.size).reshape(self.shape)
    flat_idx = property(fget=_get_flat_idx)

    def idx2flat(self, *args, **kwargs):
        
        if len(args) > 0:
            _flat_idx = self.flat_idx
            flat_idx = [_flat_idx[i] for i in args]
        elif 'idx' in kwargs:
            _flat_idx = self.flat_idx
            flat_idx = [_flat_idx[i] for i in kwargs.pop('idx')]
        elif 'flat_idx' in kwargs:
            flat_idx = np.atleast_1d(kwargs.pop('flat_idx'))
        else:
            flat_idx = range(self.size)

        return np.asarray(flat_idx).flatten()


    # Type casting
    def _get_bin(self):

        bits = np.asarray([b.bin for b in\
            self._bitarray]).reshape(self.shape)

        return bits

    bin = property(fget=_get_bin)

    def _get_float(self):
        floats = np.asarray([b.float for b in\
            self._bitarray]).reshape(self.shape)

        return floats

    float = property(fget=_get_float)

    # Bit selection generators
    def _get_rand_bit(self):
        return np.random.randint(0, self.nbits)
    rand_bit = property(fget=_get_rand_bit)

    def _get_rand_bits_section(self):
        return np.abs(np.arange(self.rand_bit) - self.nbits + 1)
    rand_bits_section = property(fget=_get_rand_bits_section)

    def _get_rand_bits_sign_and_section(self):
        bits = self.rand_bits_section
        if np.random.randint(0, 2):
            bits = np.concatenate((bits, [0]))
        return bits
    rand_bits_sign_and_section = property(fget=_get_rand_bits_sign_and_section)

    def _get_rand_bits(self):
        return np.unique(np.random.randint(0, self.nbits, self.rand_bit))
    rand_bits = property(fget=_get_rand_bits)


    # BitArray methods
    def bitarray_method(self, name, *args, **kwargs):

        inplace = kwargs.pop('inplace', True)

        if inplace:
            bs = self
        else:
            bs = copy.deepcopy(self)

        for b in bs._bitarray:
            b.__getattribute__(name)(*args, **kwargs)

        return bs

    def invert(self, **kwargs):
        pos = kwargs.pop('pos', range(self.nbits))

        flat_idx = self.idx2flat(**kwargs)
        bs = self._inplace(**kwargs) 

        if isinstance(pos, str):
            if not hasattr(self, pos):
                msg = 'pos must be an array of bit indices'
                msg += ' or a BitString attribute'
                raise ValueError(msg)

            logging.debug('Mutating with bit index generator: %s', pos)
            for i in flat_idx:
                _pos = self.__getattribute__(pos)
                logging.debug('%s: bits %s', i, _pos)
                bs._bitarray[i].invert(pos=_pos)
        else:
            logging.debug('Mutating bits %s', pos)
            for i in flat_idx:
                bs._bitarray[i].invert(pos=pos)

        return bs

    def cross(self, idx0, idx1):

        idx0 = np.asarray(idx0)
        idx1 = np.asarray(idx1)

        assert idx0.shape == idx1.shape, 'idx0 must have same shape as idx1'
       
        i0 = self.idx2flat(idx0)
        i1 = self.idx2flat(idx1)

        for i0, i1 in zip(self.idx2flat(idx0), self.idx2flat(idx1)):
            ibit = self.rand_bit

            b0 = self._bitarray[i0].bin
            b1 = self._bitarray[i1].bin

            self._bitarray[i0] = BitArray(bin=b0[0: ibit] + b1[ibit:])
            self._bitarray[i1] = BitArray(bin=b1[0: ibit] + b0[ibit:])







