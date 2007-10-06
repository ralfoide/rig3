#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Load .rc settings

Part of Rig3.
License GPL.

This a base class for settings that merely defines how to load settings, not
what they should define. Derived classes will provide accessors to the (expected)
settings to be loaded.
"""
__author__ = "ralfoide@gmail.com"

import sys
import ConfigParser

#------------------------
class SettingsBase(object):
    """
    Base class to read settings.
    This is merely a convenience wrapper on top of Python's ConfigParser.
    """
    def __init__(self, log):
        self._log = log
        self._parser = ConfigParser.SafeConfigParser()

    def Load(self, config_paths):
        parsed = self._parser.read(config_paths)
        self._log.Info("Parsed %s out of %s", parsed, config_paths)
        self._log.Debug("Defaults: %s", self._parser.defaults())
        for s in self._parser.sections():
            self._log.Debug("Section[%s]: %s", s, self._parser.items(s))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
