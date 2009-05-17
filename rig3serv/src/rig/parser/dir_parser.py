#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import os
import re

from rig.hashable import Hashable

_EXCLUDE = ".rig3-exclude"

#------------------------
class RelPath(Hashable):
    """
    Represents a 'relative' path, with a base and a relative sub path.
    The full absolute path is available too.
    """
    def __init__(self, abs_base, rel_curr):
        super(RelPath, self).__init__()
        self.abs_base = abs_base
        self.rel_curr = rel_curr
        self.abs_path = os.path.join(abs_base, rel_curr)
        self._realpath = None  # computed on demand. See realpath()

    def __eq__(self, rhs):
        if isinstance(rhs, self.__class__):
            return (self.abs_base == rhs.abs_base and
                    self.rel_curr == rhs.rel_curr and
                    self.abs_path  == rhs.abs_path)
        else:
            return False

    def rig_hash(self, md=None):
        return self.update_hash(md, self.abs_path)

    def __str__(self):
        return "[%s => %s]" % (self.abs_base, self.rel_curr)

    def __repr__(self):
        try:
            return "[%s %s => %s]" % (self.__class__.__name__,
                                      self.abs_base,
                                      self.rel_curr)
        except:
            return super(RelPath, self).__repr__()

    def basename(self):
        """
        Returns the basename of the relative portion of the path, i.e.
        the last path segment.
        """
        return os.path.basename(self.rel_curr)

    def dirname(self):
        """
        Returns the parent of the relative portion of the path, i.e.
        removes the last path segment. If there's none, the rel_curr path
        will be empty -- abs_base is never touched.

        This dies NOT modify the current object. It returns a new one
        of the *same* type.
        """
        p = RelPath.__new__(self.__class__)
        p.__init__(self.abs_base,
                   os.path.dirname(self.rel_curr))
        return p

    def join(self, *args):
        """
        Join one or more path components to the relative portion of the
        current path and returns a new RelPath-derived object for it.

        This does NOT modify the current object. It returns a new one
        of the *same* type.
        """
        p = RelPath.__new__(self.__class__)
        p.__init__(self.abs_base,
                   os.path.join(self.rel_curr, *args))
        return p

    def realpath(self):
        """
        Returns the realpath of the file or directory pointed to by this
        item.
        """
        rp = self._realpath
        if rp is None:
            rp = self._realpath = os.path.realpath(self.abs_path)
        return rp

# RelDir and RelFile are strictly equivalent to RelPath. The difference
# is purely semantic.
class RelDir(RelPath):
    """
    Represents a 'relative' directory, with a base and a relative sub directory.
    The full absolute dir path is available too.
    """
    def __init__(self, abs_base, rel_curr):
        super(RelDir, self).__init__(abs_base, rel_curr)

class RelFile(RelPath):
    """
    Represents a 'relative' file, with a base and a relative sub file.
    The full absolute file path is available too.
    """
    def __init__(self, abs_base, rel_curr):
        super(RelFile, self).__init__(abs_base, rel_curr)

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

        if isinstance(dir_pattern, (str, unicode)):
            dir_pattern = re.compile(dir_pattern)

        if isinstance(file_pattern, (str, unicode)):
            file_pattern = re.compile(file_pattern)

        abs_source_curr_dir = self._abs_source_dir

        if rel_curr_dir:
            abs_source_curr_dir = os.path.join(self._abs_source_dir, rel_curr_dir)

        self._log.Debug("Parse dir: %s", abs_source_curr_dir)

        names = self._listdir(abs_source_curr_dir)
        names = self._RemoveExclude(abs_source_curr_dir, names)

        for name in names:
            full_path = os.path.join(abs_source_curr_dir, name)
            if self._isdir(full_path):
                if dir_pattern.search(name):
                    rel_name = name
                    if rel_curr_dir:
                        rel_name = os.path.join(rel_curr_dir, name)
                    p = self._new()._ParseRec(rel_name, file_pattern, dir_pattern)
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

    def TraverseDirs(self):
        """
        Generator that traverses the directories in the directory structure.
        For each directory, returns a tuple (source_dir, dest_dir, all_files).
        Processes directories deep-first in sorted order.

        The all_files list is not sorted in any particular order.
        The all_files list can be empty if there are no interesting files in this
        directory. It's up to the caller to decide how to handle this.

        Callers should treat the tuples as immutable and not change the values.
        """
        yield (self.AbsSourceDir(), self.AbsDestDir(), self._files)
        dirs = list(self._sub_dirs)
        dirs.sort(lambda x, y: cmp(x._rel_curr_dir, y._rel_curr_dir))
        for d in dirs:
            for i in d.TraverseDirs():
                yield i

    # Utilities

    def _RemoveExclude(self, abs_root, names, _excl_file=None):
        """
        Filters a list of file names and remove those that should be excluded.

        Parameters:
        - abs_root: string, the current directory parsed
        - names: list [ str ], the names found in the directory.
        - _excl_file: A seam to allow unit test to inject a fake _EXCLUDE file.
          If not none, must support .readlines() and .close() (cf StringIO)

        If the _EXCLUDE file is found in names, read it, then use it to filter
        out files to exclude. The _EXCLUDE file is a list of regexp, one per
        line.

        Returns the filtered list, or the same list if nothing was touched.
        """
        if not names or not _EXCLUDE in names:
            return names
        names.remove(_EXCLUDE)
        try:
            if not _excl_file:
                _excl_file = file(os.path.join(abs_root, _EXCLUDE), "r")
            for regexp in _excl_file.readlines():
                r = re.compile(regexp.strip())
                n = len(names) - 1
                if n < 0:
                    break
                while n >= 0:
                    name = names[n]
                    if r.match(name):
                        self._log.Debug("Exclude file/dir: %s", os.path.join(abs_root, name))
                        names.pop(n)
                    n -= 1
        finally:
            if _excl_file:
                _excl_file.close()
        return names

    def __eq__(self, rhs):
        """
        Equality of two DirParser is defined as equality of all of its
        members, i.e. absolute directories, file list and sub dirs list.
        """
        if isinstance(rhs, DirParser):
            eq = (self.AbsSourceDir() == rhs.AbsSourceDir()
                  and self.AbsDestDir() == rhs.AbsDestDir()
                  and self.Files() == rhs.Files()
                  and self.SubDirs() == rhs.SubDirs())
            return eq
        else:
            return False

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
