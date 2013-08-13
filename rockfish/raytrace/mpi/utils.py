"""
General utilites
"""
import os

curdir = lambda: os.path.abspath(os.path.curdir)
fname = lambda path, name, ext: os.path.join(path, '{:}.{:}'.format(name, ext))
