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
        # TODO: self.GeneratePages(categories, items)
        # TODO: self.DeleteOldGeneratedItems()

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
        Traverses the source tree and generates new items as needed.
        
        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.
        
        Returns a tuple (list: categories, list: items).
        """
        categories = []
        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            self._log.Info("Process %s => %s", source_dir, 
                           dest_dir)
            if self.UpdateNeeded(source_dir, dest_dir, all_files):
                files = [f.lower() for f in all_files]
                cats = []
                items = []
                if "index.izu" in files:
                    cats, items = self.GenerateIzuEntry("index.izu", source_dir, dest_dir, all_files)
                else:
                    cats, items = self.GenerateAlbumEntry(source_dir, dest_dir, all_files)
                for c in cats:
                    if not c in categories:
                        categories.append(c)
                for i in items:
                    if not i in items:
                        items.append(i)
        return categories, items

    def UpdateNeeded(self, source_dir, dest_dir, all_files):
        """
        The item needs to be updated if the source directory or any of
        its internal files are more recent than the destination directory.
        And obviously it needs to be created if the destination does not
        exist yet.
        """
        if not os.path.exists(dest_dir):
            return true
        source_ts = None
        dest_ts = None
        try:
            dest_ts = self.DirTimeStamp(dest_dir)
        except OSError:
            return True
        try:
            source_ts = self.DirTimeStamp(source_dir)
        except OSError:
            return False
        return source_ts > dest_ts

    def GenerateIzuEntry(self, index, source_dir, dest_dir, all_files):
        """
        Generates a new Izumi entry from the given index.
        Might be associated with all images from all_files
        Returns: tuple (list: categories, list: items)
        """
        # TODO
        return [], []

    def GenerateAlbumEntry(self, source_dir, dest_dir, all_files):
        """
        Generates a new photo album entry from the given index.
        Returns: tuple (list: categories, list: items)
        """
        # TODO
        return [], []
        

    # Utilities, overridable for unit tests
    
    def DirTimeStamp(self, dir):
        """
        Returns the most recent change or modification time stamp for the
        given directory.
        
        Throws OSError with e.errno==errno.ENOENT (2) when the directory
        does not exists.
        """
        c = os.path.getctime(dir)
        m = os.path.getmtime(dir)
        return max(c, m)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
