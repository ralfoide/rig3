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
        tree = Parse()
        categories, items = GenerateItems(source_tree)
        # GeneratePages(categories, items)

    def Parse(self):
        p = DirParser(self._log).Parse(os.path.realpath(self._source_dir),
                                       os.path.realpath(self._dest_dir),
                                       _DIR_PATTERN, _VALID_FILES)
        return p
    
    def GenerateItems(self, tree):
        for source_dir, dest_dir, filename, all_files in tree.Traverse():
            self._log.Info("Process %s/%s => %s/%s", source_dir, filename,
                           dest_dir, filename)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
