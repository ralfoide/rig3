#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Load .rc settings

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


This a base class for settings that merely defines how to load settings, not
what they should define. Derived classes will provide accessors to the (expected)
settings to be loaded.
"""
__author__ = "ralfoide at gmail com"

import sys
from ConfigParser import RawConfigParser

#------------------------
class SettingsBase(object):
    """
    Base class to read settings.
    This is merely a convenience wrapper on top of Python's RawConfigParser.

    Note that we don't use ConfigParser since we don't want variable expansion.
    At the contrary some variables contain %(name)s that should not be expanded.
    """
    def __init__(self, log):
        self._log = log
        self._parser = RawConfigParser()

    def Load(self, config_paths):
        """
        Loads sites .rc files from the list of config_paths.
        Return self, for chaining.
        """
        parsed = self._parser.read(config_paths)
        self._log.Info("Parsed %s out of %s", parsed, config_paths)
        self._log.Debug("Defaults: %s", self._parser.defaults())
        for s in self._parser.sections():
            self._log.Debug("Section[%s]: %s", s, self._parser.items(s))
        return self

    def ConfigParser(self):
        """
        Returns the underlying ConfigParser instance.
        """
        return self._parser

    def Items(self, site_name):
        """
        Returns all the variables defined for the given site name.
        This returns them as a dictionary { var: value }.

        By contrast, the default RawConfigParser.items() returns them as a
        list of tuples.
        """
        return dict(self._parser.items(site_name))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
