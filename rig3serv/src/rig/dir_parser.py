#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

#------------------------
class DirParser(object):
    """
    Describe class
    """
    def __init__(self, log, abs_source_dir, abs_dest_dir):
        self._log = log
        self._abs_source_dir = abs_source_dir
        self._abs_dest_dir = abs_dest_dir
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

    def Parse(self, dir_pattern, file_pattern):
        root_dir = self._abs_source_dir
        dest_dir = self._abs_dest_dir
        self._log.Debug("Parse dir: %s", root_dir)
        names = self._listdir(root_dir)
        for name in names:
            full_path = os.path.join(root_dir, name)
            if self._isdir(full_path):
                if dir_pattern.search(name):
                    p = Dir(self._log, full_path, os.path.join(dest_dir, name))
                    p.Parse(dir_pattern, file_pattern)
                    # Skip empty sub-dirs
                    if p.Files() or p.SubDirs():
                        self.SubDirs().append(p)
                        self._log.Debug("Append dir: %s", full_path)
                    else:
                        self._log.Debug("Ignore empty dir: %s", full_path)
                else:
                    self._log.Debug("Ignore dir: %s", full_path)
            else:
                if file_pattern.search(name):
                    self.Files().append(full_path)
                    self._log.Debug("Append file: %s=%s", p, full_path)
                else:
                    self._log.Debug("Ignore file: %s", full_path)

    # Overridable methods for mock unittest

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
