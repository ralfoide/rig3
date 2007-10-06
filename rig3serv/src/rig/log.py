#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3: log module.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re
import sys
import logging

_NAME = "rig"
_FILENAME = "default.log"

_SKIP_PATH_RE = re.compile(r"(?:logging[/\\]__init__\.py|rig[/\\]log\.py)$")

#------------
class _LogFormatter(logging.Formatter):
  """
  Overrides logging.Formatter to add our specific keywords
  """

  def __init__(self, fmt=None, datefmt=None):
    logging.Formatter.__init__(self, fmt, datefmt)

  def format(self, record):
    """
    Override logging.Formatter.format() in order to correctly set the
    %(lineno)s, %(filename)s, %(module)s and %(pathname)s variables. The
    original caller's filename as detected by the logging module will always be
    this file, rig.helper.Log, whereas we want the caller of the rig's Log
    module. We simply recompute the values and store them in the record's
    object where it will be picked up by the string formatter.
    """
    f = sys._getframe(1)
    while f:
      co = f.f_code
      pathname = os.path.normcase(co.co_filename)

      # skip ourselves and the logging module calls
      if _SKIP_PATH_RE.search(pathname) is None:
        # got the first "real" caller, update the record
        record.lineno = f.f_lineno
        record.pathname = pathname
        try:
          record.filename = os.path.basename(pathname)
          record.module = os.path.splitext(record.filename)[0]
        except:
          pass
        break
      f = f.f_back

    return logging.Formatter.format(self, record)



#------------
class Log:
    """
    A simple wrapper around Python's logging facility.
    """

    def __init__(self,
                 name=_NAME,
                 file=_FILENAME,
                 use_stderr=True,
                 format="%(levelname)s %(filename)s:%(lineno)s [%(asctime)s] %(message)s",
                 date="%Y/%m/%d %H:%M:%S"):
        """
        Configures (or reconfigures) the logger with this information.
    
        The 'file' argument can be a string: the filename of where to log to
        (opened as rw). Otherwise it is a file-like object, i.e. a stream which
        would be an already opened file or a StringIO object.
        
        'file' can also be None, in which case this creates a logger that does
        actually not log anything. Mostly useful for quiet unit tests.
    
        Set 'use_stderr' to false to prevent the logger from output to sys.stderr.
        This is the default. It is detected if 'file' is also set to sys.stderr to
        avoid logging twice to stderr.
    
        This convenience method allows the unit test to override some parameters,
        most notably the file argument.
        """
        self._logger = logger = logging.getLogger(name)
        self.is_verbose = False
    
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
        if isinstance(file, str):
            h = logging.FileHandler(file)
        else:
            h = logging.StreamHandler(file)
        logger.addHandler(h)
        h.setFormatter(_LogFormatter(format, date))
    
        if file != sys.stderr and use_stderr:
            h = logging.StreamHandler(sys.stderr)
            logger.addHandler(h)
            h.setFormatter(_LogFormatter(format, date))

        logger.setLevel(self.is_verbose and logging.DEBUG or logging.WARNING)

        # Log ourselves
        self.Info("Logging enabled: %s", str(file))

    def Close(self):
        """
        Shutdown the logger.
        """
        if self._logger:
            logging.shutdown()
            self._logger = None

    def SetVerbose(self, verbose):
        """
        Set the logger to verbose (debug level) or normal (warning level).
        """
        self.is_verbose = verbose
    
        assert(self._logger)
        self._logger.setLevel(verbose and logging.DEBUG or logging.WARNING)

    def IsVerbose(self):
        """
        Indicates if the logger is in verbose mode (debug-level) or
        normal mode (warning-level).
        """
        return self.is_verbose

    def Debug(self, msg, *args):
        """
        Log a debug-level message.
    
        This will be logged only when IsVerbose is true.
        """
        self._logger.debug(msg, *args)

    def Info(self, msg, *args):
        """
        Log an info-level message.
    
        This will be logged only when IsVerbose is true.
        """
        self._logger.info(msg, *args)

    def Warning(self, msg, *args):
        """
        Log a warning-level message.
    
        This will be logged whether IsVerbose is false or true.
        """
        self._logger.warning(msg, *args)

    # Warn is a synonym for Warning
    Warn = Warning

    def Error(self, msg, *args):
        """
        Log an error-level message.
    
        This will be logged whether IsVerbose is false or true.
        """
        self._logger.error(msg, *args)

    def Exception(self, msg, *args):
        """
        Log an exception-level message.
    
        This will be logged whether IsVerbose is false or true.
        """
        self._logger.exception(msg, *args)

    def Log(self, level, msg, *args):
        """
        Log a message with a specific level.
    
        Level should be one of the logging's module levels:
        logging.DEBUG, logging.WARNING, logging.INFO, logging.ERROR.
    
        This is similar to calling any of the corresponding convenience
        methods except the level can be made dynamic at runtime.
    
        Log levels DEBUG and INFO have no effect unless IsVerbose is true.
        """
        self._logger.log(level, msg, *args)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
