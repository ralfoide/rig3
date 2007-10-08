#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site definition and actions

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import os
import sys

from rig.dir_parser import DirParser

_DIR_PATTERN = re.compile(r"^(?P<year>\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
_VALID_FILES = re.compile(r"\.(?:izu|jpe?g)$")

#------------------------
class Site(object):
    """
    Describes on site and what we can do with it.
    """
    def __init__(self, log, public_name, source_dir, dest_dir, theme):
        self._log = log
        self._public_name = public_name
        self._source_dir = source_dir
        self._dest_dir = dest_dir
        self._theme = theme
    
    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """
        self._log.Info("Processing site %s.\nSource: %s\nDest: %s\nTheme: %s",
                       self._public_name, self._source_dir, self._dest_dir, self._theme)
        tree = self.Parse(self._source_dir, self._dest_dir)
        categories, items = self.GenerateItems(tree)
        # GeneratePages(categories, items)

    def Parse(self, source_dir, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.
        
        Returns the DirParser pointing on the root of the source tree.
        
        TODO: make dir/file patterns configurable in SitesSettings.
        """
        p = DirParser(self._log).Parse(os.path.realpath(source_dir),
                                       os.path.realpath(dest_dir),
                                       file_pattern=_VALID_FILES,
                                       dir_pattern=_DIR_PATTERN)
        return p
    
    def GenerateItems(self, tree):
        """
        Traverses the source tree and generate new items as needed.
        
        Returns a tuple (list: categories, list: items).
        """
        categories = []
        items = []
        for source_dir, dest_dir, filename, all_files in tree.TraverseFiles():
            self._log.Info("Process %s/%s => %s/%s", source_dir, filename,
                           dest_dir, filename)
            if self.UpdateNeeded(source_dir, dest_dir):
                pass
        return categories, items

    def UpdateNeeded(self, source_dir, dest_dir):
        pass


    # Utilities, overridable for unit tests
    

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
