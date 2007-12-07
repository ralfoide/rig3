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
import errno

from rig.parser.dir_parser import DirParser, RelDir
from rig.parser.izu_parser import IzuParser
from rig.template.template import Template
from rig.version import Version

DEFAULT_THEME = "default"


#------------------------
class SiteItem(object):
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
class SiteBase(object):
    """
    Base class to generate sites.
    
    This class is "abstract". Some methds must be derived to define a proper behavior.
    """
    MEDIA_DIR = "media"
    DIR_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
    VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")

    def __init__(self, log, dry_run, settings):
        self._log = log
        self._dry_run = dry_run
        self._settings = settings
        self._izu_parser = IzuParser(self._log)

    # Derived class must implement this to define the desired behavoior

    def MakeDestDirs(self):
        """
        Creates the necessary directories in the destination.

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        
        Returns self for chaining

        Subclassing: Derived classes SHOULD override this. Parent does nothing.        
        """
        return self

    def GeneratePages(self, categories, items):
        """
        - categories: list of categories accumulated from each entry
        - items: list of SiteItem

        Subclassing: Derived classes MUST override this and not call the parent.
        """
        raise NotImplementedError("Must be derived by subclasses")

    def GenerateItem(self, source_dir, all_files):
        """
        Generates a new photoblog entry, which may have an index and/or may have an album.
        Returns a SiteItem or None

        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)

        Subclassing: Derived classes MUST override this and not call the parent.
        """
        raise NotImplementedError("Must be derived by subclasses")

    # Generic implementation that is not expected to be derived.

    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """
        self._log.Info("[%s] Processing site:\n  Source: %s\n  Dest: %s\n  Theme: %s",
                       self._settings.public_name, self._settings.source_dir, self._settings.dest_dir, self._settings.theme)
        self.MakeDestDirs()
        self._CopyMedia()
        tree = self._Parse(self._settings.source_dir, self._settings.dest_dir)
        categories, items = self.GenerateItems(tree)
        self.GeneratePages(categories, items)
        # TODO: self.DeleteOldGeneratedItems()

    def _CopyMedia(self):
        """
        Copy media directory from selected template to destination

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        """
        _keywords = { "base_url": self._settings.base_url,
                    "public_name": self._settings.public_name }
        def _apply_template(source, dest):
            # Use fill template to copy/transform the file
            template = Template(self._log, file=source)
            result = template.Generate(_keywords)
            fdest = file(dest, "wb")
            fdest.write(result)
            fdest.close()

        media = os.path.join(self._TemplateDir(), self._settings.theme, self.MEDIA_DIR)
        if os.path.isdir(media):
            self._CopyDir(media, os.path.join(self._settings.dest_dir, self.MEDIA_DIR),
                          filter_ext={ ".css": _apply_template })

    def _Parse(self, source_dir, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        
        Returns the DirParser pointing on the root of the source tree.
        
        TODO: make dir/file patterns configurable in SitesSettings.
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

    def _TemplateDir(self):
        f = __file__
        return os.path.realpath(os.path.join(os.path.dirname(f), "..", "..", "templates"))

    def _MkDestDir(self, rel_dir):
        """
        Creates a directory in the site's dest_dir.
        Doesn't generate an error if the directory already exists.
        """
        try:
            os.makedirs(os.path.join(self._settings.dest_dir, rel_dir))
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def _CopyDir(self, source_dir, dest_dir,
                 skip=[ "CVS", ".svn" ],
                 filter_ext={}):
        """
        Copies a directory (recursively, with all its content) into
        a given destination. OVerwrites existing content. This doesn't
        clean the output so it will merge with existing content, if any.
        Also it will fail if:
        - the destination is not a directory
        - the destination is not writable/executable
        
        filter_ext is a dict { extension => filter_method }.
        Methods should have a signature (source_name, dest_name) and should
        copy the source to the dest, using whatever transformation desired.
        Extensions must start with dot in them (i.e. ".css", not "css")
        
        This automatically skips CVS and .svn directories.
        """
        # create dest dir
        try:
            os.makedirs(dest_dir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        files = os.listdir(source_dir)
        for name in files:
            if name in skip:
                continue
            ps = os.path.join(source_dir, name)
            ext = os.path.splitext(name)[1]
            if os.path.isdir(ps):
                self._CopyDir(ps, os.path.join(dest_dir, name), skip, filter_ext)
            elif ext in filter_ext or ("." + ext) in filter_ext:
                # use a filter to copy from source to dest
                filter_ext[ext](ps, os.path.join(dest_dir, name))
            else:
                # regular file copy
                dest = file(os.path.join(dest_dir, name), "wb")
                source = file(ps, "rb")
                s = source.read(4096)
                while len(s):
                    dest.write(s)
                    s = source.read(4096)
                source.close()
                dest.close()

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
