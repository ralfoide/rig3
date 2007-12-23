#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from datetime import datetime

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
        super(SourceItem, self).__init__(date)
        self.source_dir = source_dir
        self.all_files = all_files

# TODO: SourceFile, SourceBlog
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
