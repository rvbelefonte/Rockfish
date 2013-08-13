"""
Logging facility for Rockfish
"""
import logging
import logging.config
from rockfish.config import LOGGING_CONF_FILE


class NullHandler(logging.Handler):
    """
    Do-nothing handler for loggerless applications
    """
    def emit(self, record):
        pass

logging.config.fileConfig(LOGGING_CONF_FILE)
h = NullHandler()
logging.getLogger("root").addHandler(h)



if __name__ == "__main__":

    # example application code
    for name in ['root', 'foo.bar', __name__]:
        print "Logger output using '{:}':".format(name)
    
        logger = logging.getLogger(name)

        logger.debug("debug message")
        logger.info("info message")
        logger.warn("warn message")
        logger.error("error message")
        logger.critical("critical message")
