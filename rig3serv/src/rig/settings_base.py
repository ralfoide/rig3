#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Load .rc settings

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import sys
import ConfigParser

#------------------------
class SettingsBase:
    """
    Describe class
    """
    def __init__(self, log):
        self._log = log
        self._parser = ConfigParser.SafeConfigParser()
    
    def Load(self, config_paths):
        parsed = self._parser.read(config_paths)
        self._log.Warn("Parsed %s out of %s", parsed, config_paths)
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
