"""
Genetic algorithm for acoustic location of ocean instruments.

Example 1
=========

Define some example data:

    >>> sx = [-86.5, -86.512, -86.23, -86.12] # source x-coords
    >>> sy = [10.12, 10.123, 10.213, 10.522] # source y-coords
    >>> sz = [0.006, 0.006, 0.006, 0.006] # source depths
    >>> t = [1.54, 1.23, 1.75, 1.6] # one-way travel times

Create the population evolver with default parameters:

    >>> from acousticsurvey.genetic import Environment
    >>> env = Environment(sx, sy, sz, t)

Plot RMS for the initial population:

    >>> env.plot_rms() # doctest:+SKIP

Plot positions:

    

Reproduce, mutate, and crossover the population:

    >>> import matplotlib.pyplot as plt
    >>> fig = plt.figure()
    >>> ax1 = fig.add_subplot(121)
    >>> env.plot_map(ax=ax1, show=False)
    >>> env.population.reproduce()
    >>> env.population.crossover(0.5)
    >>> env.population.mutate(0.5)
    >>> ax2 = fig.add_subplot(122)
    >>> env.plot_map(ax=ax2, show=True)


"""
import numpy as np
import matplotlib.pyplot as plt
import logging
import warnings
from acousticsurvey.traveltimes import slant_time
from acousticsurvey.binary import crossover, mutate

# XXX
#logging.basicConfig(level=logging.DEBUG)

# Initial values
VLIMITS = (1200., 1800.)
ZLIMITS = (0., 6000.)

class Environment(object):
    """
    Class for handling an evolving population of ocean instrument positions.
    """
    def __init__(self, source_x, source_y, source_z, travel_times,
                 velocity=None,
                 xlimits=None, ylimits=None, zlimits=ZLIMITS,
                 vlimits=VLIMITS,
                 population_size=100, mutation_probability=0.25, 
                 crossover_probability=0.25, 
                 crs={'epsg':4326}):
        """
        Creates an initial population of canidate positions with methods
        for evolving the population.

        :param source_x, source_y: Lists of horizontal source positions for
            each travel time in ``travel_times``. Units are set by the
            coordinate reference system paremeter ``crs``.
        :param source_z: List of source depths in meters below a vertical 
            datum (set by ``crs``) for each travel time in ``travel_times``. 
        :param travel_times: List of one-way travel times in seconds for 
            water-wave arrivals.
        :param xy_region: Optional. Tuple of ``(xmin, xmax, ymin, ymax)``
            values that define the horizonal-coordinate search region.
            Default is to create an initial population in the vicinity of 
            the source positions and allow the population to evolve away 
            from these positions.
        :param z_range: Optional. Tuple of ``(zmin, zmax)`` values that limit
            the range of possible depth values. Units are meters. Default is
            ``(0., 6000.)``.
        :param velocity: Optional. Value of an average water velocity in 
            meters per second. Default is include average velocity as a 
            parameter in the genetic algorithm.
        :param population_size: Optional.  Number of individuals in the
            genetic algorithm.  Default is ``100``.
        :param mutation_probability: Optional. Probablity that mutations
            will occur. Default is ``0.25``.
        :param crossover_probability: Optional. Probablity that crossover
           will occur. Default is ``0.25``.
        :param crs: Optional. Dictionary of values for the coordinate
            reference system of input and output data. Default is geographic
            using the WGS84 ellipsoid and vertical datum (EPSG 4326).
        """
        # Attach data to class instance
        self.data = Data(source_x, source_y, source_z, travel_times)
        # Attach parameters
        self.velocity = velocity
        self.XLIMITS = xlimits
        self.YLIMITS = ylimits
        self.ZLIMITS = zlimits
        self.VLIMITS = vlimits
        self.CROSSOVER_PROBABILITY = crossover_probability
        self.MUTATION_PROBABILITY = mutation_probability
        # Set ranges for initial population
        if xlimits is None:
            xrange = (min(self.data.x), max(self.data.x))
        else:
            xrange = xlimits
        if ylimits is None:
            yrange = (min(self.data.y), max(self.data.y))
        else:
            yrange = ylimits
        if zlimits is None:
            zrange = ZLIMITS 
        else:
            zrange = zlimits
        if vlimits is None:
            vrange = VLIMITS 
        else:
            vrange = vlimits
        # Create the initial population
        self.population = Population(xrange, yrange, zrange, vrange,
                                     size=population_size) 
        # Evaluate initial population
        self.evaluate()

    def plot_map(self, ax=None, show=True):
        """
        Plot positions on a map.

        .. note:: Coordinates are plotted as cartesian coordiantes, regardless
            of the coordinate reference system.

        :param ax: Optional. :class:`matplotlib.axis.Axis` to plot into.
            Default is to create and show a new figure.
        """
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)  
        ax.plot(self.population.x, self.population.y, '.b')
        ax.plot(self.data.x, self.data.y, '*r')
        ax.plot(self.result['x'], self.result['y'], '^g')
        plt.xlabel('Easting')
        plt.ylabel('Northing')
        # Show the plot
        if show:
            plt.show()

    def plot_rms(self, fig=None, show=True):
        """
        Plot an overview of RMS and parameter values.

        :param fig: Optional. :class:`matplotlib.figure.Figure` to plot into.
            Default is to create and show a new figure.
        """
        if fig is None:
            fig = plt.figure()
        else:
            fig.clear()
        # Easting 
        ax = fig.add_subplot(221)
        ax.plot(self.population.x, self.population.rms, '.b')
        ax.plot(self.result.x, self.result.rms, 'og')
        plt.xlabel('Easting')
        plt.ylabel('RMS (s)')
        # Northing
        ax = fig.add_subplot(222)
        ax.plot(self.population.y, self.population.rms, '.b')
        ax.plot(self.result.y, self.result.rms, 'og')
        plt.xlabel('Northing')
        plt.ylabel('RMS (s)')
        # Plot depth
        ax = fig.add_subplot(223)
        ax.plot(self.population.z, self.population.rms, '.b')
        ax.plot(self.result.z, self.result.rms, 'og')
        plt.xlabel('Depth (m)')
        plt.ylabel('RMS (s)')
        # Plot velocity
        ax = fig.add_subplot(224)
        ax.plot(self.population.v, self.population.rms, '.b')
        ax.plot(self.result.v, self.result.rms, 'og')
        plt.xlabel('Velocity (m/s)')
        plt.ylabel('RMS (s)')
        # Show the plot
        if show:
            plt.show()

    def evaluate(self):
        """
        Evaulate the entire population.
        """
        # Calculate error and rms for all positions
        self.population.rms = []
        self.population.e_mean = []
        for rx, ry, rz, v in zip(self.population.x, self.population.y,
                                 self.population.z, self.population.v):
            e = []
            for sx, sy, sz, t in zip(self.data.x, self.data.y, self.data.z,
                                     self.data.t):
                tpred = slant_time(sx, sy, sz, rx, ry, rz, v)
                e.append(np.abs(tpred - t))
            self.population.e_mean.append(np.mean(e))
            self.population.rms.append(np.sqrt(np.mean(np.asarray(e)**2)))
        # Select best position
        i = np.asarray(self.population.rms).argmin()
        self.result = {'x':self.population.x[i],
                       'y':self.population.y[i],
                       'z':self.population.z[i],
                       'v':self.population.v[i],
                       'rms':self.population.rms[i],
                       'e_mean':self.population.e_mean[i]}

    def evolve(self, target_rms=0.001, max_generations=1000,
               crossover_probability=0.10, mutation_probability=0.10,
               plot=False):
        """
        Evolve the population to locate the instrument.

        :param target_rms: Optional. Target root-mean-square error.
            Default is 0.001.
        :param max_generations: Optional.  Maximum number of generations
            to produce before stopping. Default is 1000.
        :param mutation_probability: Optional. Probablity that mutations
            will occur. Default is ``0.25``.
        :param crossover_probability: Optional. Probablity that crossover
           will occur. Default is ``0.25``.
        :param plot: Optional. Determines whether or not plot population at
            each generation. Default is False.
        """
        i = 0
        while i < max_generations:
            # Print current RMS and plot
            print 'Generation {:010d}: RMS={:}'.format(i, self.result['rms'])
            # Plot current generation
            if plot is True:
                # TODO just update exisiting plot, don't create a new plot
                self.plot_map()
            # Compare current rms to target rms
            if self.result['rms'] <= target_rms:
                return self.result
            # Create a new generation
            self.population.reproduce()
            self.population.crossover(probability=crossover_probability)
            self.population.mutate(probability=mutation_probability)
            # Evauluate the new generation
            self.evaluate()
            i += 1
        msg = 'Reached {:} generations without reaching target RMS.'\
                .format(i-1)
        msg += '  Returning most recent result with RMS={:}.'\
                .format(self.result['rms'])
        warnings.warn(msg)
        return self.result

class Data(object):
    """
    Convenience class for handling travel-time data.
    """
    def __init__(self, x, y, z, t):
        """
        :param x, y: Lists of horizontal source positions for
            each travel time in ``travel_times``.
        :param z: List of source depths in meters below a vertical 
            datum for each travel time in ``travel_times``. 
        :param t: List of one-way travel times in seconds for 
            water-wave arrivals.
        """
        self.x = x
        self.y = y
        self.z = z
        self.t = t

class Population(object):
    """
    Convenience class for handling the population of canidate locations.
    """
    def __init__(self, xrange, yrange, zrange, vrange, size=100):
        """
        Initialize the population with random values.

        :param xrange: Tuple of ``(xmin, xmax)``.
        :param yrange: Tuple of ``(ymin, ymax)``.
        :param zrange: Tuple of ``(zmin, zmax)``.
        :param vrange: Tuple of ``(vmin, vmax)``.
        :param size: Optional. Number of individuals in the population.
            Default is 100.
        """
        self.x = self._init(size, xrange[0], xrange[1])
        self.y = self._init(size, yrange[0], yrange[1])
        self.z = self._init(size, zrange[0], zrange[1])
        self.v = self._init(size, vrange[0], vrange[1])
        self.rms = np.asarray([None for i in range(size)])
        self.size = size
        if vrange[0] == vrange[1]:
            self.EVOLVE_VELOCITY = False
        else:
            self.EVOLVE_VELOCITY = True

    def _init(self, size, minval, maxval):
        """
        Creates a list of random values.

        :param minval, maxval: Minimum and maximum of the output values.
        :param n: Number of values to output.
        :returns: List of random values.
        """
        if minval == maxval:
            return minval * np.ones(size)
        else:
            return np.mean([minval, maxval]) \
                    + (np.random.rand(size)-0.5)*(maxval-minval)

    def reproduce(self):
        # get idx, rms sorted by fitness
        fitness = 1./np.asarray(self.rms)
        isort = np.argsort(fitness)
        idx = [range(self.size)[i] for i in isort]
        fitness = np.asarray([fitness[i] for i in isort])
        # Determine number of children from each point 
        cumfitness = np.cumsum(fitness)
        rd = np.sort(np.random.rand(self.size)*np.sum(fitness))
        nchild = [np.sum(np.nonzero(rd < cumfitness[0]))]
        #logging.debug('#%i gets %i children', idx[0], nchild[-1])
        for i in range(1, self.size):
            nchild.append(np.sum((rd < cumfitness[i])*
                                 (rd > cumfitness[i-1])))
            #logging.debug('#%i gets %i children',
            #              idx[i], nchild[-1])
        #logging.debug('Total children = %i', np.sum(nchild))
        # Reproduce
        #TODO self._reproduce(idx, nchild)

    def crossover(self, probability=0.25):
        """
        Introduce crossovers into the population.

        :param probability: Optional. Probabilty that cross over will occur.
            Default is ``0.25``.
        """
        for i in np.nonzero(np.random.rand(self.size) <= probability)[0]:
            # randomly select two individuals for cross over
            ip = np.round(np.random.rand(2)*self.size-1)
            #logging.debug('Crossing #%i with #%i:', *ip)
            #logging.debug('    #%i: x=%f, y=%f, z=%f, v=%f',
            #              ip[0], self.x[ip[0]], self.y[ip[0]], self.z[ip[0]],
            #              self.v[ip[0]])
            #logging.debug('    #%i: x=%f, y=%f, z=%f, v=%f',
            #              ip[1], self.x[ip[1]], self.y[ip[1]], self.z[ip[1]],
            #              self.v[ip[1]])
            self.x[ip[0]] = crossover(self.x[ip[0]], self.x[ip[1]])
            self.y[ip[0]] = crossover(self.y[ip[0]], self.x[ip[1]])
            self.z[ip[0]] = crossover(self.z[ip[0]], self.x[ip[1]])
            if self.EVOLVE_VELOCITY is True:
                self.v[ip[0]] = crossover(self.v[ip[0]], self.v[ip[1]])
            #logging.debug('>>> #%i: x=%f, y=%f, z=%f, v=%f',
            #              ip[0], self.x[ip[0]], self.y[ip[0]], self.z[ip[0]],
            #              self.v[ip[0]])

    def mutate(self, probability=0.25):
        """
        Introduce mutations into the population.

        :param probability: Optional. Probabilty that any one individual will 
            mutate. Default is ``0.25``.
        """
        for i in np.nonzero(np.random.rand(self.size) <= probability)[0]:
            logging.debug('Mutating #%i: x=%f, y=%f, z=%f, v=%f',
                          i, self.x[i], self.y[i], self.z[i], self.v[i])
            self.x[i] = mutate(self.x[i])
            self.y[i] = mutate(self.y[i])
            self.z[i] = mutate(self.z[i])
            if self.EVOLVE_VELOCITY is True:
                 self.v[i] = mutate(self.v[i])
            logging.debug('>>>>>>>>>>>>  x=%f, y=%f, z=%f, v=%f',
                          self.x[i], self.y[i], self.z[i], self.v[i])

if __name__ == "__main__":
    import doctest
    doctest.testmod()
