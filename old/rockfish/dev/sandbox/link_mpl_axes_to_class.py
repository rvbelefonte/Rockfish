"""
Goal: associate a matplotlib.axes instance with a class.
"""
import unittest
import matplotlib.pyplot as plt
import matplotlib

class Example(object):

    def __init__(self, ax):
        self.ax = ax

    def plot(self):
        self.ax.plot([0,1],[0,1])

class ExampleTestCase(unittest.TestCase):

    def test_link_axes(self):
        """
        Class functions should be able to make changes to the axes.
        """
        # create our own axes
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # pass them to class init
        myinstance = Example(ax)
        # class instance should have axis instance 
        self.assertTrue(isinstance(myinstance.ax, matplotlib.axes.Axes))
        # should be able to plot directly to the axes
        myinstance.ax.plot([0,1],[0,1])
        self.assertEqual(len(myinstance.ax.lines), 1)
        # class should be able to update the axes
        myinstance.plot()
        self.assertEqual(len(myinstance.ax.lines), 2)
        # updates outside the class should be seen inside the class
        ax.plot([0,1],[0,1])
        self.assertEqual(len(myinstance.ax.lines), 3)
        self.assertEqual(len(ax.lines), 3)
        
def suite():
    return unittest.makeSuite(ExampleTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


