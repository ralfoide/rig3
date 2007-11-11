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
class RelDir(object):
    """
    Represents a 'relative' directory, with a base and a relative sub directory.
    The full absolute dir path is available too. 
    """
    def __init__(self, abs_base, rel_curr):
        self.abs_base = abs_base
        self.rel_curr = rel_curr
        self.abs_dir = os.path.join(abs_base, rel_curr)

    def __eq__(self, rhs):
        if isinstance(rhs, RelDir):
            return (self.abs_base == rhs.abs_base and
                    self.rel_curr == rhs.rel_curr and
                    self.abs_dir  == rhs.abs_dir)
        return super(RelDir, self).__eq__(rhs)


#------------------------
class DirParser(object):
    """
    Parses directories recursively accordingly to given file/dir regexps.
    Parses the source directories and match the corresponding destination
    structure (destination is not checked for existence.)
            
    Note that SubDirs() and Files() are already sorted alphabetically.
    This helps remove differences between various file systems.

    To use create the object then call Parse() on it.
    """
    def __init__(self, log, abs_source_dir=None, abs_dest_dir=None):
        self._log = log
        self._files = []
        self._sub_dirs = []
        self._abs_source_dir = abs_source_dir
        self._abs_dest_dir = abs_dest_dir
        self._rel_curr_dir = None

    def AbsSourceDir(self):
        """
        Returns a RelDir that describes the source directory (source + relative + absolute)
        """
        return RelDir(self._abs_source_dir, self._rel_curr_dir)

    def AbsDestDir(self):
        """
        Returns a RelDir that describes the destination directory (source + relative + absolute)
        """
        return RelDir(self._abs_dest_dir, self._rel_curr_dir)

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
        self._abs_source_dir = abs_source_dir
        self._abs_dest_dir = abs_dest_dir
        return self._ParseRec("", file_pattern, dir_pattern)

    def _ParseRec(self, rel_curr_dir, file_pattern=".", dir_pattern="."):
        """
        Implementation helper for Parse().
        Most arguments are the same, see Parse(), except:
        - abs_dest_dir_base: the original dest_dir given to Parse().
        - rel_curr_dest_dir: the relative current dest_dir
        """
        self._files = []
        self._sub_dirs = []
        self._rel_curr_dir = rel_curr_dir
        if isinstance(dir_pattern, str):
            dir_pattern = re.compile(dir_pattern)
        if isinstance(file_pattern, str):
            file_pattern = re.compile(file_pattern)
        abs_source_curr_dir = self._abs_source_dir
        if rel_curr_dir:
            abs_source_curr_dir = os.path.join(self._abs_source_dir, rel_curr_dir)
        self._log.Debug("Parse dir: %s", abs_source_curr_dir)
        names = self._listdir(abs_source_curr_dir)
        for name in names:
            full_path = os.path.join(self._abs_source_dir, name)
            if self._isdir(full_path):
                if dir_pattern.search(name):
                    rel_name = name
                    if rel_curr_dir:
                        rel_name = os.path.join(rel_curr_dir, name)
                    p = self._new()._ParseRec(name, file_pattern, dir_pattern)
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
        self._files.sort()
        self._sub_dirs.sort(cmp=lambda x, y: cmp(x._rel_curr_dir, y._rel_curr_dir))
        return self

    def TraverseFiles(self):
        """
        Generator that traverses all files in the directory structure.
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
            yield (self._abs_source_dir,
                   self._abs_dest_dir, self._rel_curr_dir,
                   f, all_files)
        dirs = list(self._sub_dirs)
        dirs.sort(lambda x, y: cmp(x.AbsSourceDir(), y.AbsSourceDir()))
        for d in dirs:
            for i in d.TraverseFiles():
                yield i

    def TraverseDirs(self):
        """
        Generator that traverses the directories in the directory structure.
        For each directory, returns a tuple (source_dir, dest_dir, all_files).
        Processes directories deep-first in sorted order.
        The all_files list is not sorted in any particular order.
        Callers should treat the tuples as immutable and not change the values.
        """
        yield (self.AbsSourceDir(), self.AbsDestDir(), self._files)
        dirs = list(self._sub_dirs)
        dirs.sort(lambda x, y: cmp(x.AbsSourceDir(), y.AbsSourceDir()))
        for d in dirs:
            for i in d.TraverseDirs():
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

    def _new(self):
        """
        Creates a new DirParser instance. Useful for mock unittests.
        """
        return DirParser(self._log, self._abs_source_dir, self._abs_dest_dir)

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
