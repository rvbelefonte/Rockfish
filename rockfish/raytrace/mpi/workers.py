"""
Worker-side functions
"""
import os
from mpi4py import MPI
from rockfish import logging, TraveltimeDatabaseConnection
from rockfish.raytrace.shortest_path import raytrace_from_ascii
from utils import curdir, fname


logger = logging.getLogger(__name__)

class RaytraceWorker(object):
    """
    Worker-side raytracer
    """
    def __init__(self, db, vmfile, **kwargs):
        
        if type(db) is not TraveltimeDatabaseConnection:
            raise TypeError(
                'db must be a rockfish.TraveltimeDatabaseConnection')

        self.NAME = MPI.Get_processor_name()
        self.RANK = MPI.COMM_WORLD.Get_rank()
        self.ID = kwargs.pop('id', '{:05d}'.format(self.RANK))
        self.db = db
        self.VM_FILE = vmfile
        self.OPTIONS = kwargs.pop('options', {})
        self.PICK_KEYS = kwargs.pop('pick_keys', {})
        self.OUTPUT_DIR = kwargs.pop('output_dir', curdir())

        logger.info('Created raytracing worker with ID {:}'.format(self.ID))
        logger.debug(
            "Using traveltime database of type {:} connected to '{:}'."\
            .format(type(db).__name__, db.__file__))
        self._log_values()

    def setup(self):
        """
        Setup input files for the raytracer
        """
        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)

        self.db.write_vmtomo(instfile=self.REC_FILE, pickfile=self.PICK_FILE,
                             shotfile=self.SRC_FILE, directory=None,
                             **self.PICK_KEYS)

    def run(self):
        """
        Run the raytracer
        """
        logger.info('Starting worker {:}...'.format(self.ID))
        raytrace_from_ascii(self.VM_FILE, self.RAY_FILE,
                            instfile=self.REC_FILE, shotfile=self.SRC_FILE,
                            pickfile=self.PICK_FILE, **self.OPTIONS)
        logger.info('Worker {:} finished.'.format(self.ID))

    def _log_values(self, attr=['NAME', 'RANK', 'ID', 'OUTPUT_DIR',
                                'VM_FILE', 'REC_FILE', 'SRC_FILE', 'PICK_FILE',
                                'RAY_FILE', 'PICK_KEYS', 'OPTIONS']):
        for k in attr:
            logger.debug('{:} = {:}'.format(k, self.__getattribute__(k)))



    # Properties
    def _get_recfile(self):
        return fname(self.OUTPUT_DIR, self.ID, 'rec')
    REC_FILE = property(fget=_get_recfile)
    
    def _get_srcfile(self):
        return fname(self.OUTPUT_DIR, self.ID, 'src')
    SRC_FILE = property(fget=_get_srcfile)

    def _get_pickfile(self):
        return fname(self.OUTPUT_DIR, self.ID, 'pick')
    PICK_FILE = property(fget=_get_pickfile)

    def _get_rayfile(self):
        return fname(self.OUTPUT_DIR, self.ID, 'ray')
    RAY_FILE = property(fget=_get_rayfile)

