#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Note: SourceReaderBase derived classes defined here are created in SitesSettings._ProcessSources()

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re
from datetime import datetime

from rig.source_item import SourceDir
from rig.parser.dir_parser import DirParser

#------------------------
class SourceReaderBase(object):
    """
    Base class for a source reader, i.e. an object that knows how to read
    "items" out of files or directories on disk. These items (...TODO...)
    
    The constructor captures the current site settings and the default source
    path. The settings are used for specific configuration, for example
    filtering patterns.
    """
    def __init__(self, log, settings, path):
        self._log = log
        self._path = path
        self._settings = settings

    def GetPath(self):
        return self._path

    def Parse(self, dest_dir):
        """
        Parses the source and returns a list of SourceItem.
        The source directory is always the internal path given to the
        constructor of the source reader.
        
        Parameter:
        - dest_dir (string): Destination directory.
        
        This method is abstract and must always be implemented by derived
        classes. Derived classes should not call their super.
        """
        raise NotImplementedError("Must be derived by subclasses")

    def __eq__(self, rhs):
        """
        Two readers are equal if they have the same type, the same path
        and the same settings.
        """
        if isinstance(rhs, SourceReaderBase):
            return (type(self) == type(rhs) and
                    self._path == rhs._path and
                    self._settings == rhs._settings)
        else:
            return False
    
    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self._path)


#------------------------
class SourceDirReader(SourceReaderBase):
    """
    Source reader for rig3 directory-based entries.
    
    Only directories are considered as items: valid directory names must match
    the specified DIR_PATTERN regexp *and* must contain one or more of the files
    specified by the VALID_FILES regexp.
    """

    DIR_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
    VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")

    def __init__(self, log, settings, path):
        # TODO: the patterns must be overridable via site settings
        super(SourceDirReader, self).__init__(log, settings, path)

    def Parse(self, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.

        Then traverses the source tree and generates new items as needed.
        
        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.
        
        Parameter:
        - dest_dir (string): Destination directory.
        
        Returns a list of SourceItem.
        """
        tree = DirParser(self._log).Parse(os.path.realpath(self.GetPath()),
                                          os.path.realpath(dest_dir),
                                          file_pattern=self.VALID_FILES,
                                          dir_pattern=self.DIR_PATTERN)
 
        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            if all_files:
                # Only process directories that have at least one file of interest
                self._log.Debug("[%s] Process '%s' to '%s'",
                                self._settings and self._settings.public_name or "[Unnamed Site]",
                               source_dir.rel_curr, dest_dir.rel_curr)
                if self._UpdateNeeded(source_dir, dest_dir, all_files):
                    date = datetime.fromtimestamp(self._DirTimeStamp(source_dir.abs_dir))
                    item = SourceDir(date, source_dir, all_files)
                    items.append(item)
        return items


    # Utilities, overridable for unit tests

    def _UpdateNeeded(self, source_dir, dest_dir, all_files):
        """
        The item needs to be updated if the source directory or any of
        its internal files are more recent than the destination directory.
        And obviously it needs to be created if the destination does not
        exist yet.
        
        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        - dest_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        """
        if not os.path.exists(dest_dir.abs_dir):
            return True
        source_ts = None
        dest_ts = None
        try:
            dest_ts = self._DirTimeStamp(dest_dir.abs_dir)
        except OSError:
            self._log.Info("[%s] Dest '%s' does not exist", self._settings.public_name,
                           dest_dir.abs_dir)
            return True
        try:
            source_ts = self._DirTimeStamp(source_dir.abs_dir)
        except OSError:
            self._log.Warn("[%s] Source '%s' does not exist", self._settings.public_name,
                           source_dir.abs_dir)
            return False
        return source_ts > dest_ts

    def _DirTimeStamp(self, dir):
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
class SourceFileReader(SourceReaderBase):
    """
    Source reader for file-based entries.
    
    Only files which name match the specified FILE_PATTERN regexp are considered valid.
    """

    FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *\.(?P<ext>izu|html)$")

    def __init__(self, log, settings, path):
        # TODO: the patterns must be overridable via site settings
        super(SourceDirReader, self).__init__(log, settings, path)

    def Parse(self, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.

        Then traverses the source tree and generates new items as needed.
        
        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.
        
        Parameter:
        - dest_dir (string): Destination directory.
        
        Returns a list of SourceItem.
        """
        items = []        
        if FILE_PATTERN.search(self.path):
            self._log.Debug("[%s] Process '%s' to '%s'",
                            self._settings and self._settings.public_name or "[Unnamed Site]",
                           source_dir.rel_curr, dest_dir.rel_curr)
            date = datetime.fromtimestamp(self._FileTimeStamp(source_dir.abs_dir))
            item = SourceDir(date, source_dir, all_files)
            items.append(item)
        return items


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
