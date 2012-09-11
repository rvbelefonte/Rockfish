"""
Module for handling message printing by Rockfish.
"""

import sys

codeCodes = {
	'black':	'0;30',		'bright gray':	'0;37',
	'blue':		'0;34',		'white':		'1;37',
	'green':	'0;32',		'bright blue':	'1;34',
	'cyan':		'0;36',		'bright green':	'1;32',
	'red':		'0;31',		'bright cyan':	'1;36',
	'purple':	'0;35',		'bright red':	'1;31',
	'yellow':	'0;33',		'bright purple':'1;35',
	'dark gray':'1;30',		'bright yellow':'1;33',
	'normal':	'0'
}

class Colors:
    """
    Standardized colors.
    """

    HEADER = "\033["+codeCodes['black']+"m"
    OKPURPLE = "\033["+codeCodes['purple']+"m"
    OKBLUE = "\033["+codeCodes['blue']+"m"
    OKGREEN = "\033["+codeCodes['green']+"m"
    WARNING = "\033["+codeCodes['purple']+"m"
    FAIL = "\033["+codeCodes['red']+"m"
    ENDC = "\033["+codeCodes['normal']+"m"

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

class ProgressPercentTicker(Colors):
    """
    Simple progress indicator.

    Prints progress as: [X%] <name>.
    """

    def __init__(self,name,maxval,complete=0):
        """
        :param name: Name to be appended to progress.
        :param maxval: Value at end of progress.
        :param complete: Optional.  Value currently completed. 
        """
        print "       " + name,
        self.MAXVAL = maxval
        self.update(complete)

    def update(self,complete,color=None):
        """
        Updates the progress indicator.

        :param complete: Optional.  Value currently completed. 
        """
        if not color:
            color = self.OKPURPLE
        fmt = color + "[%i%%]" + self.ENDC
        sys.stdout.write('\r')
        sys.stdout.write(fmt % self._percent_done(complete))
        sys.stdout.flush()

    def finish(self):
        """
        Prints a new line character.
        """
        self.update(self.MAXVAL,color=self.OKGREEN)

    def _percent_done(self,complete):
        """
        Calculate percent complete.

        :param complete: Value completed.
        """
        return float(complete)/self.MAXVAL * 100.



