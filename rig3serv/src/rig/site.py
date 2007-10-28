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
import zlib
import errno
from datetime import datetime

from rig.parser.dir_parser import DirParser
from rig.parser.izu_parser import IzuParser
from rig.template.template import Template

DEFAULT_THEME = "default"
INDEX_IZU = "index.izu"
_DIR_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
_VALID_FILES = re.compile(r"\.(?:izu|jpe?g)$")
_DATE_YMD= re.compile(r"^(?P<year>\d{4})[/-]?(?P<month>\d{2})[/-]?(?P<day>\d{2})"
                      r"(?:[ ,:/-]?(?P<hour>\d{2})[:/-]?(?P<min>\d{2})(?:[:/-]?(?P<sec>\d{2}))?)?")
_ITEMS_DIR = "items"
_ITEMS_PER_PAGE = 20      # TODO make a site.rc pref
_MANGLED_NAME_LENGTH = 50 # TODO make a site.rc pref

#------------------------
class _Item(object):
    """
    Represents an item:
    - list of categories (list of string)
    - date (datetime)
    - rel_filename: filename of the generated file relative to the site's
                    dest_dir.
    """
    def __init__(self, date, rel_filename, categories=None):
        self.date = date
        self.categories = categories or []
        self.rel_filename = rel_filename

    def SetContent(self, content):
        self.content = content
        return self


#------------------------
class Site(object):
    """
    Describes on site and what we can do with it.
    """
    def __init__(self, log, dry_run, public_name, source_dir, dest_dir, theme):
        self._log = log
        self._dry_run = dry_run
        self._public_name = public_name
        self._source_dir = source_dir
        self._dest_dir = dest_dir
        self._theme = theme

    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """
        self._log.Info("[%s] Processing site:\n  Source: %s\n  Dest: %s\n  Theme: %s",
                       self._public_name, self._source_dir, self._dest_dir, self._theme)
        self.MakeDestDirs()
        tree = self.Parse(self._source_dir, self._dest_dir)
        categories, items = self.GenerateItems(tree)
        self.GeneratePages(categories, items)
        # TODO: self.DeleteOldGeneratedItems()

    def MakeDestDirs(self):
        """
        Creates the necessary directories in the destination.
        """
        self._MkDestDir(_ITEMS_DIR)            

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
        
        Returns a tuple (list: categories, list: _Item).
        """
        categories = []
        items = []
        for source_dir, dest_dir, curr_dir, all_files in tree.TraverseDirs():
            self._log.Info("[%s] Process '%s' to '%s'", self._public_name,
                           source_dir, curr_dir)
            if self.UpdateNeeded(source_dir, os.path.join(dest_dir, curr_dir),
                                 all_files):
                files = [f.lower() for f in all_files]
                item = self.GenerateItem(source_dir, curr_dir, all_files)
                if item is None:
                    continue
                for c in item.categories:
                    if not c in categories:
                        categories.append(c)
                items.append(item)
        self._log.Info("[%s] Found %d items, %d categories", self._public_name,
                       len(items), len(categories))
        return categories, items

    def GeneratePages(self, categories, items):
        """
        - categories: list of categories accumulated from each entry
        - items: list of _Item
        """
        categories.sort()
        items.sort(lambda x, y: cmp(x.date, y.date))

        self.GeneratePageAll(categories, items)
        # TODO: self.GeneratePageCategory(category, items)
        # TODO: self.GeneratePageMonth(month, items)

    def GeneratePageAll(self, categories, items):
        """
        Generates pages will all items, from most recent to least recent.

        - categories: list of categories accumulated from each entry
        - items: list of _Item
        """
        prev_url = None
        next_url = None
        n = len(items)
        np = n / _ITEMS_PER_PAGE
        i = 0
        for p in xrange(0, np + 1):
            url = "index%s.html" % (p > 0 and p or "")
            if p < np:
                next_url = "index%s.html" % (p + 1)
            else:
                next_url = None
            entries = [j.content for j in items[i:i + _ITEMS_PER_PAGE] ]
            i += _ITEMS_PER_PAGE
            content = self._FillTemplate(self._theme, url,
                                         title="All Items",
                                         entries=entries,
                                         prev_url=prev_url,
                                         next_url=next_url,
                                         curr_page=p + 1,
                                         max_page=np + 1)
            self._WriteFile(content, self._dest_dir, url)
            prev_url = url

    def UpdateNeeded(self, source_dir, dest_dir, all_files):
        """
        The item needs to be updated if the source directory or any of
        its internal files are more recent than the destination directory.
        And obviously it needs to be created if the destination does not
        exist yet.
        """
        if not os.path.exists(dest_dir):
            return True
        source_ts = None
        dest_ts = None
        try:
            dest_ts = self._DirTimeStamp(dest_dir)
        except OSError:
            self._log.Info("[%s] Dest '%s' does not exist", self._public_name,
                           dest_dir)
            return True
        try:
            source_ts = self._DirTimeStamp(source_dir)
        except OSError:
            self._log.Warn("[%s] Source '%s' does not exist", self._public_name,
                           source_dir)
            return False
        return source_ts > dest_ts

    def GenerateItem(self, source_dir, rel_dest_dir, all_files):
        """
        Generates a new photoblog entry, which may have an index and/or may have an album.
        Returns an _Item or None
        """
        title = os.path.basename(source_dir)
        date = self._DateFromTitle(title) or datetime.today()
        if INDEX_IZU in all_files:
            parser = IzuParser(self._log)
            izu_file= os.path.join(source_dir, INDEX_IZU)
            self._log.Info("[%s] Render '%s' to HMTL", self._public_name,
                           izu_file)
            html, tags, cats, images = parser.RenderFileToHtml(izu_file)
            content = self._FillTemplate(self._theme, "entry.html",
                                         title=title,
                                         text=html,
                                         image="")
            filename = self._SimpleFileName(os.path.join(rel_dest_dir, INDEX_IZU))
            assert self._WriteFile(content,
                                   os.path.join(self._dest_dir, _ITEMS_DIR),
                                   filename)
            dest = os.path.join(_ITEMS_DIR, filename)
            return _Item(date, dest, categories=[]).SetContent(content)
        return None

    # Utilities, overridable for unit tests
    
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

    def _WriteFile(self, data, dest_dir, leafname):
        """
        Writes the given data to the given directory and leaf name.
        
        If you need the leafname to be sanitized (i.e. if used later in
        URLs), then call _SimpleFileName first.
        
        If data is None or anything empty (list, string, whatever), it will
        generate an empty file, but a file should be created nonetheless.
        Otherwise data can be anything that can be formatted with str().
        The file is open in binary mode so data need not be human-readable text.
        
        If the destination exists, it will be overwritten.
        
        Returns the actual full pathname written to.
        
        This method is extracted so that it can be mocked in unit tests.
        """
        dest_file = os.path.join(dest_dir, leafname)
        self._log.Info("[%s] Write %s", self._public_name, dest_file)
        if not self._dry_run:
            pass
        return dest_file

    def _SimpleFileName(self, leafname, maxlen=_MANGLED_NAME_LENGTH):
        """
        Sanitizes a file name or a path name to a single filename compatible
        with a URL with no need for fancy URL escaping.
        - Aggregates multiples "separators" such as spaces or dashes into single dashes.
        - Aggregates non-alphanums into single underscores.
        - If the name is too long, keep a shorter version with a CRC at the end.
        Returns the new file name.
        """
        name = re.sub(r"[ /\\-]+", "-", leafname)
        name = re.sub(r"[^a-zA-Z0-9-]+", "_", name)
        if len(name) > maxlen:
            # The adler32 crc is returned as an int and can thus "seem" negative
            # convert to its true long 64-bit value, always positive
            crc = zlib.adler32(leafname) & 0x0FFffFFffL
            crc = "%8x" % crc
            if name.endswith("_"):
                name = name[:maxlen - len(crc)] + crc
            else:
                name = name[:maxlen - 1 - len(crc)] + "_" + crc
        return name

    def _FillTemplate(self, theme, template, **keywords):
        """
        Renders the given template with the given theme.
        Keywords are the special variables expected by the given template.
        Returns the generated HTML as a string.
        """
        template_file = os.path.join(self._TemplateDir(), theme, template)
        template = Template(self._log, file=template_file)
        result = template.Generate(keywords)
        return result

    def _TemplateDir(self):
        f = __file__
        return os.path.realpath(os.path.join(os.path.dirname(f), "..", "..", "templates"))

    def _DateFromTitle(self, title):
        """
        Parses the date out of a title.
        Returns a datetime object or None.
        """
        m = _DATE_YMD.match(title)
        if m:
            return datetime(int(m.group("year" ) or 0),
                            int(m.group("month") or 0),
                            int(m.group("day"  ) or 0),
                            int(m.group("hour" ) or 0),
                            int(m.group("min"  ) or 0),
                            int(m.group("sec"  ) or 0))
        return None

    def _MkDestDir(self, rel_dir):
        """
        Creates a directory in the site's dest_dir.
        Doesn't generate an error if the directory already exists.
        """
        try:
            os.mkdir(os.path.join(self._dest_dir, rel_dir))
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
