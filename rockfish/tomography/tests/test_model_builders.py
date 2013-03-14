"""
Test suite for the model_builders module.
"""
import unittest
import numpy as np
from scipy.interpolate import interp1d
from rockfish.tomography.model import VM
from rockfish.tomography.model_builders import add_layers


class model_buildersTestCase(unittest.TestCase):
    """
    Test cases for the model_builders module
    """
    def test_add_layers(self):
        """
        Should add a set of new layers to a model.
        """
        # should add interfaces at constant depths
        vm = VM()
        self.assertEqual(vm.nr, 0)
        h = [2, 5, 10]
        add_layers(vm, h)
        self.assertEqual(vm.nr, 3)
        for i, _h in enumerate(h):
            self.assertEqual(vm.rf[i].min(), _h)
            self.assertEqual(vm.rf[i].max(), _h)
        # should add interface at variable depth
        vm = VM()
        self.assertEqual(vm.nr, 0)
        x2z = interp1d([vm.r1[0], vm.r2[0]], [2, 5])
        h = [[[_z] for _z in x2z(vm.x)]]
        add_layers(vm, h)
        self.assertEqual(vm.nr, 1)
        for z0, z1 in zip(h[0], vm.rf[0]):
            self.assertEqual(z0, z1)
        # should add interfaces and set layer velocities
        vm = VM()
        h = [2, 5, 10]
        v = [(VM.define_stretched_layer_velocities, [1.5, 2]),
             None, None]
        add_layers(vm, h, v)
        self.assertEqual(vm.nr, 3)
        idx = np.nonzero(vm.layers == 1)
        self.assertAlmostEqual(vm.sl[idx].min(), 1./2., 1)
        self.assertAlmostEqual(vm.sl[idx].max(), 1./1.5, 1)







def suite():
    return unittest.makeSuite(model_buildersTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
