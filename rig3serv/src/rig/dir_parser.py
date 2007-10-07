#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re

#------------------------
class DirParser(object):
    """
    Parses directories recursively accordingly to given file/dir regexps.
    Parses the source directories and match the corresponding destination
    structure (destinaton is not checked for existence.)
    
    To use create the object then call Parse() on it.
    """
    def __init__(self, log):
        self._log = log
        self._files = []
        self._sub_dirs = []
    
    def AbsSourceDir(self):
        return self._abs_source_dir
    
    def AbsDestDir(self):
        return self._abs_dest_dir
    
    def Files(self):
        return self._files
    
    def SubDirs(self):
        return self._sub_dirs

    def Parse(self, abs_source_dir, abs_dest_dir, file_pattern=".", dir_pattern="."):
        """
        Parse the directory at abs_source_dir and associate it with the parallel
        structure at abs_dest_dir. Fills Files() and SubDirs().
        
        dir_pattern and file_pattern are regular expressions (string or compiled regexp)
        to limit the directories or files accepted. Patterns are matched using "re.search",
        not "re.match" so you have to use ^..$ if you want to test against full strings.
        The default patterns are "." which matches anything.
        
        Returns self for chaining.
        """
        self._files = []
        self._sub_dirs = []
        self._abs_source_dir = abs_source_dir
        self._abs_dest_dir = abs_dest_dir
        if isinstance(dir_pattern, str):
            dir_pattern = re.compile(dir_pattern)
        if isinstance(file_pattern, str):
            file_pattern = re.compile(file_pattern)
        root_dir = self._abs_source_dir
        dest_dir = self._abs_dest_dir
        self._log.Debug("Parse dir: %s", root_dir)
        names = self._listdir(root_dir)
        for name in names:
            full_path = os.path.join(root_dir, name)
            if self._isdir(full_path):
                if dir_pattern.search(name):
                    p = self._new().Parse(full_path, os.path.join(dest_dir, name),
                                          file_pattern, dir_pattern)
                    # Skip empty sub-dirs
                    if p.Files() or p.SubDirs():
                        self._sub_dirs.append(p)
                        self._log.Debug("Append dir: %s", full_path)
                    else:
                        self._log.Debug("Ignore empty dir: %s", full_path)
                else:
                    self._log.Debug("Ignore dir: %s", full_path)
            else:
                if file_pattern.search(name):
                    self._files.append(name)
                    self._log.Debug("Append file: %s", full_path)
                else:
                    self._log.Debug("Ignore file: %s", full_path)
        return self

    def Traverse(self):
        """
        Generate that traverses the directory structure.
        Returns a tuple (source_dir, dest_dir, leaf_name, all_files) for each file.
        all_files is the current list of files for this directory. It's a copy
        so the caller can remove elements to be processed next and can use it
        to lookup specific files ahead.
        Processes local files then each subdirectories in alphabetical
        order.
        """
        all_files = list(self._files)
        all_files.sort()
        for f in all_files:
            yield (self._abs_source_dir, self._abs_dest_dir, f, all_files)
        dirs = list(self._sub_dirs)
        dirs.sort(lambda x, y: cmp(x.AbsSourceDir(), y.AbsSourceDir()))
        for d in dirs:
            for i in d.Traverse():
                yield i

    # Utilities

    def __eq__(self, other):
        """
        Equality of two DirParser is defined as equality of all of its
        members, i.e. absolute directories, file list and sub dirs list.
        """
        eq = (self.AbsSourceDir() == other.AbsSourceDir()
              and self.AbsDestDir() == other.AbsDestDir()
              and self.Files() == other.Files()
              and self.SubDirs() == other.SubDirs())
        return eq

    def __ne__(self, other):
        """
        See DirParser.__eq__
        """
        return not self.__eq__(other)

    def __repr__(self):
        return "%s[%s => %s, files: %s, subdirs: %s]" % (
            super(DirParser, self).__repr__(),
            self.AbsSourceDir(), self.AbsDestDir(),
            self.Files(), self.SubDirs())

    # Overridable methods for mock unittest

    def _new(self, leaf):
        """
        Creates a new DirParser instance. Useful for mock unittests.
        """
        return DirParser(self._log)

    def _listdir(self, dir):
        """
        Returns os.listdir(dir). Useful for mock unittests.
        Returns [] for invalid directories.
        """
        try:
            return os.listdir(dir)
        except OSError:
            self._log.Exception("listdir error on '%s'", dir)
            return []

    def _isdir(self, dir):
        """
        Returns os.path.isdir(dir). Useful for mock unittests.
        Returns False on OS Errors.
        """
        try:
            return os.path.isdir(dir)
        except OSError:
            self._log.Exception("isdir error on '%s'", dir)
            return False

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
