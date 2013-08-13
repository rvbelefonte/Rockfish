"""
Parallel raytracing using MPI
"""
from mpi4py import MPI
from rockfish import logging, TraveltimeDatabaseConnection
from rockfish.database.utils import format_search
from rockfish.raytrace.mpi import workers
from utils import curdir

logger = logging.getLogger(__name__)

class RaytraceMaster(object):
    """
    Master raytracer
    """
    def __init__(self, db, vmfile, **kwargs):

        if type(db) is not TraveltimeDatabaseConnection:
            raise TypeError(
                'db must be a rockfish.TraveltimeDatabaseConnection')

        self.db = db
        self.VM_FILE = vmfile
        self.OPTIONS = kwargs.pop('options', {})
        self.PICK_KEYS = kwargs.pop('pick_keys', {})
        self.OUTPUT_DIR = kwargs.pop('output_dir', curdir())

        self.DISTRIBUTE_KEYS = kwargs.pop('distribute_keys',
                                          ['event', 'rid'])

        self.workers = []


    def distribute(self):
        """
        Distribute raytracing jobs
        """
        dist_keys = {}
        for k in self.DISTRIBUTE_KEYS:
            if k in self.PICK_KEYS:
                dist_keys[k] = self.PICK_KEYS[k]

        sql = 'SELECT DISTINCT '
        assert len(self.DISTRIBUTE_KEYS) > 0,\
                'len(DISTRIBUTE_KEYS) must be greater than 0'
        sql += ', '.join(self.DISTRIBUTE_KEYS)
        sql += ' FROM picks'
    
        if len(dist_keys) > 0:
            sql += ' WHERE ' + format_search(dist_keys, list_op='OR',
                                             key_op='AND')

        dat = self.db.execute(sql).fetchall()
        nworkers = len(dat)
        logging.info('Distributing picks between {:} worker(s)'\
                     .format(nworkers))

        self.workers = []
        for iworker, row in enumerate(dat):
            keys = dict(self.PICK_KEYS.items())
            for i, k in enumerate(self.DISTRIBUTE_KEYS):
                keys[k] = [row[i]]

            logging.debug('pick keys for worker {:}: {:}'\
                          .format(iworker, keys))

            rt = workers.RaytraceWorker(self.db, self.VM_FILE, 
                                        options=self.OPTIONS,
                                        pick_keys=keys, 
                                        output_dir=self.OUTPUT_DIR,
                                        id='{:05d}'.format(iworker))
            self.workers.append(rt)





    def run(self):
        """
        Execute the parallel raytracing jobs
        """
        pass


