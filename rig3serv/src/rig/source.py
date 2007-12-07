#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"


#------------------------
class SourceItem(object):
    """
    Represents an item:
    - list of categories (list of string)
    - content: the data of the file
    - date (datetime)
    - rel_filename: filename of the generated file relative to the site's
                    dest_dir.
    """
    def __init__(self, date, rel_filename, content, categories=None):
        self.date = date
        self.content = content
        self.categories = categories or []
        self.rel_filename = rel_filename


#------------------------
class SourceBase(object):
    """
    Base class for a source, i.e. an object that knows how to read "items"
    out of files or directories on disk. These items
    """
    def __init__(self, log, path):
        self._log = log
        self._path = path

    def GetPath(self):
        return self._path

    def Parse(self, source_dir, dest_dir):
        """
        Returns a list of SiteItem
        """
        return []

#------------------------
class SourceDirItems(SourceBase):
    def __init__(self, log, path):
        super(SourceDirItems, self).__init__(log, path)

    def Parse(self, source_dir, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.
        """
        p = DirParser(self._log).Parse(os.path.realpath(source_dir),
                                       os.path.realpath(dest_dir),
                                       file_pattern=self.VALID_FILES,
                                       dir_pattern=self.DIR_PATTERN)
        return p

    def GenerateItems(self, tree):
        """
        Traverses the source tree and generates new items as needed.
        
        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.
        
        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        
        Returns a tuple (list: categories, list: SiteItem).
        """
        categories = []
        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            self._log.Debug("[%s] Process '%s' to '%s'", self._settings.public_name,
                           source_dir.rel_curr, dest_dir.rel_curr)
            if self._UpdateNeeded(source_dir, dest_dir, all_files):
                files = [f.lower() for f in all_files]
                item = self.GenerateItem(source_dir, all_files)
                if item is None:
                    continue
                for c in item.categories:
                    if not c in categories:
                        categories.append(c)
                items.append(item)
        self._log.Info("[%s] Found %d items, %d categories", self._settings.public_name,
                       len(items), len(categories))
        return categories, items


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
