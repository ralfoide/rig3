#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from datetime import datetime
from rig.parser.dir_parser import RelDir, RelFile

#------------------------
class SourceItem(object):
    """
    Abstract base class to represents an item:
    - list of categories (list of string)
    - date (datetime)

    The class is conceptually abstract, meaning it has no data.
    In real usage, clients will process derived classes (e.g. SourceDir)
    which have members with actual data to process.
    """
    def __init__(self, date, categories=None):
        self.date = date
        self.categories = categories or []

    def __eq__(self, rhs):
        return (isinstance(rhs, SourceItem) and
                self.date == rhs.date and
                self.categories == rhs.categories)

#------------------------
class SourceDir(SourceItem):
    """
    Represents a directory item from a SourceDirReader.
    
    Such a directory generally contains an index.izu or index.html
    and a bunch of image files.

    Paremeters:
    - date (datetime): Date of the directory (i.e. most recent item)
    - source_dir (RelDir): absolute+relative source directory
    - all_files (list [string]): All interesting files in this directory
    """
    def __init__(self, date, source_dir, all_files):
        super(SourceDir, self).__init__(date)
        self.source_dir = source_dir
        self.all_files = all_files

    def __eq__(self, rhs):
        if not super(SourceDir, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceDir) and
                self.source_dir == rhs.source_dir and
                self.all_files == rhs.all_files)

    def __repr__(self):
        return "<%s (%s) %s, %s, %s>" % (self.__class__.__name__,
                                          self.date,
                                          self.source_dir,
                                          self.all_files,
                                          self.categories)

#------------------------
class SourceFile(SourceItem):
    """
    Represents a file item from a SourceFileReader.
    
    Paremeters:
    - date (datetime): Date of the file
    - source_file (RelFile): absolute+relative source file
    """
    def __init__(self, date, source_file):
        super(SourceFile, self).__init__(date)
        self.source_file = source_file

    def __eq__(self, rhs):
        if not super(SourceFile, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceFile) and
                self.source_file == rhs.source_file)

    def __repr__(self):
        return "<%s (%s) %s, %s, %s>" % (self.__class__.__name__,
                                          self.date,
                                          self.source_file,
                                          self.categories)


# TODO:  SourceBlog
#    - content: the data of the file
#    - rel_filename: filename of the generated file relative to the site's
#                    dest_dir.



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
