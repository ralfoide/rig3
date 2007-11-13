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
import cgi
import sys
import zlib
import errno
import urllib
from datetime import datetime

from rig.parser.dir_parser import DirParser, RelDir
from rig.parser.izu_parser import IzuParser
from rig.template.template import Template
from rig.version import Version

DEFAULT_THEME = "default"
INDEX_IZU = "index.izu"
INDEX_HTML = "index.html"
_MEDIA_DIR = "media"
_DIR_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
_VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")
_DATE_YMD= re.compile(r"^(?P<year>\d{4})[/-]?(?P<month>\d{2})[/-]?(?P<day>\d{2})"
                      r"(?:[ ,:/-]?(?P<hour>\d{2})[:/.-]?(?P<min>\d{2})(?:[:/.-]?(?P<sec>\d{2}))?)?")
_ITEMS_DIR = "items"
_ITEMS_PER_PAGE = 20      # TODO make a site.rc pref
_MANGLED_NAME_LENGTH = 50 # TODO make a site.rc pref

_TEMPLATE_NEED_ITEM_FILES = False # TODO make a site.rc pref

_IMG_PATTERN = re.compile(r"^(?P<index>[A-Z]?\d{2,})(?P<rating>[ \._+=-])(?P<name>.+?)"
                          r"(?P<ext>\.(?:jpe?g|(?:original\.|web\.)mov|(?:web\.)wmv|mpe?g|avi))$")

_RATING_BASE = -2
_RATING_BAD = -1
_RATING_DEFAULT = 0
_RATING_GOOD = 1
_RATING_EXCELLENT = 2
_RATING = { ".": _RATING_BAD,
            "_": _RATING_DEFAULT,
            "-": _RATING_GOOD,
            "+": _RATING_EXCELLENT }

#------------------------
class _Item(object):
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
class Site(object):
    """
    Describes on site and what we can do with it.
    """
    def __init__(self, log, dry_run, settings):
        self._log = log
        self._dry_run = dry_run
        self._settings = settings
        self._izu_parser = IzuParser(self._log)

    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """
        self._log.Info("[%s] Processing site:\n  Source: %s\n  Dest: %s\n  Theme: %s",
                       self._settings.public_name, self._settings.source_dir, self._settings.dest_dir, self._settings.theme)
        self._MakeDestDirs()
        self._CopyMedia()
        tree = self._Parse(self._settings.source_dir, self._settings.dest_dir)
        categories, items = self._GenerateItems(tree)
        self._GeneratePages(categories, items)
        # TODO: self.DeleteOldGeneratedItems()

    def _MakeDestDirs(self):
        """
        Creates the necessary directories in the destination.
        """
        self._MkDestDir(_ITEMS_DIR)            

    def _CopyMedia(self):
        """
        Copy media directory from selected template to destination
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

        media = os.path.join(self._TemplateDir(), self._settings.theme, _MEDIA_DIR)
        if os.path.isdir(media):
            self._CopyDir(media, os.path.join(self._settings.dest_dir, _MEDIA_DIR),
                          filter_ext={ ".css": _apply_template })

    def _Parse(self, source_dir, dest_dir):
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
    
    def _GenerateItems(self, tree):
        """
        Traverses the source tree and generates new items as needed.
        
        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.
        
        Returns a tuple (list: categories, list: _Item).
        """
        categories = []
        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            self._log.Info("[%s] Process '%s' to '%s'", self._settings.public_name,
                           source_dir.rel_curr, dest_dir.rel_curr)
            if self._UpdateNeeded(source_dir, dest_dir, all_files):
                files = [f.lower() for f in all_files]
                item = self._GenerateItem(source_dir, all_files)
                if item is None:
                    continue
                for c in item.categories:
                    if not c in categories:
                        categories.append(c)
                items.append(item)
        self._log.Info("[%s] Found %d items, %d categories", self._settings.public_name,
                       len(items), len(categories))
        return categories, items

    def _GeneratePages(self, categories, items):
        """
        - categories: list of categories accumulated from each entry
        - items: list of _Item
        """
        categories.sort()
        # Sort by decreasing date (i.e. compares y to x, not x to y)
        items.sort(lambda x, y: cmp(y.date, x.date))

        self._GeneratePageAll(categories, items)
        # TODO: self.GeneratePageCategory(category, items)
        # TODO: self.GeneratePageMonth(month, items)

    def _GeneratePageAll(self, categories, items):
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
            
            entries = []
            older_date = None
            for j in items[i:i + _ITEMS_PER_PAGE]:
                entries.append(j.content)
                older_date = (older_date is None) and j.date or max(older_date, j.date)
            i += _ITEMS_PER_PAGE

            keywords = self._settings.AsDict()
            keywords["title"] = "All Items"
            keywords["entries"] = entries
            keywords["prev_url"] = prev_url
            keywords["next_url"] = next_url
            keywords["curr_page"] = p + 1
            keywords["max_page"] = np + 1
            keywords["last_gen_ts"] = datetime.today()
            keywords["last_content_ts"] = older_date
            version = Version()
            keywords["rig3_version"] = "%s.%s" % (version.VersionString(),
                                                  version.SvnRevision())
            
            content = self._FillTemplate("index.html", **keywords)
            self._WriteFile(content, self._settings.dest_dir, url)
            prev_url = url

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

    def _GenerateItem(self, source_dir, all_files):
        """
        Generates a new photoblog entry, which may have an index and/or may have an album.
        Returns an _Item or None

        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        """
        title = os.path.basename(source_dir.rel_curr)
        date = self._DateFromTitle(title) or datetime.today()
        main_filename = ""
        sections = {}
        tags = {}
        if INDEX_IZU in all_files:
            main_filename = INDEX_IZU
            izu_file = os.path.join(source_dir.abs_dir, INDEX_IZU)
            self._log.Info("[%s] Render '%s' to HMTL", self._settings.public_name,
                           izu_file)
            tags, sections = self._izu_parser.RenderFileToHtml(izu_file)
        #elif INDEX_HTML in all_files:
        # -----------------DEBUG--------------------
        #    main_filename = INDEX_HTML
        #    html_file = os.path.join(source_dir.abs_dir, INDEX_HTML)
        #    sections["html"] = self._ReadFile(html_file)
        #    tags = self._izu_parser.ParseFirstLine(sections["html"])
        else:
            self._log.Error("No content for source %s", source_dir)
            return None

        cats = tags.get("cat", [])
        date = tags.get("date", date)     # override directory's date
        title = tags.get("title", title)  # override directory's title

        if not "images" in sections:
            html_img = self._GenerateImages(source_dir, all_files)
            if html_img:
                sections["images"] = html_img

        keywords = self._settings.AsDict()
        keywords["title"] = title
        keywords["sections"] = sections
        keywords["date"] = date
        keywords["tags"] = tags
        keywords["categories"] = cats
        content = self._FillTemplate("entry.html", **keywords)
        filename = self._SimpleFileName(os.path.join(source_dir.rel_curr, main_filename))
        if _TEMPLATE_NEED_ITEM_FILES:
            assert self._WriteFile(content,
                                   os.path.join(self._settings.dest_dir, _ITEMS_DIR),
                                   filename)
        dest = os.path.join(_ITEMS_DIR, filename)
        return _Item(date, dest, content=content, categories=cats)

    def _GenerateImages(self, source_dir, all_files):
        """
        Generates a table with images.
        
        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)

        Heuristics:
        - if rating+ images are present, show them with a width of 400 or 300
        - if rating- images are present, show them as thumbnails
        - otherwise, simply returns a link on the album (TODO later: sample based on date)
        - if there are no files that look suitable for rig, returns None
        
        Also, Rig-specific stuff:
        - all links point on the albums (i.e. parent directory)
        - The image pattern means there might be several variations
          (.jpg/.mov) for the same image index. For movies, uses the
          snapshot if present. 
        
        TODO: currently has a lot of hardcoded things that should go into
        site-dependent prefs.
        """
        images = {}
        # images: index => { "top_rating": number,
        #                    "files": [ pattern.groupdict + "full": leaf name ] }
        num_excellent = 0
        num_good = 0
        num_images = 0 
        for filename in all_files:
            m = _IMG_PATTERN.match(filename)
            if m:
                num_images += 1
                index = m.group("index")
                entry = images[index] = images.get(index, { "top_rating": _RATING_BASE, "top_name": None, "files": [] })
                rating = self._GetRating(m.group("rating"))
                num_good += (rating == _RATING_GOOD and 1 or 0)
                num_excellent += (rating == _RATING_EXCELLENT and 1 or 0)
                if rating > entry["top_rating"]:
                    entry["top_rating"] = rating
                    entry["top_name"] = filename
                entry["files"].append(filename)
        
        links = []
        if num_excellent:
            size = 400
            if num_excellent > 2:
                size = min(200, 800 / num_excellent)
            num_col = min(num_excellent, 4)
            keys = images.keys()
            keys.sort()
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == _RATING_EXCELLENT:
                    links.append(self._GetRigLink(source_dir, entry["top_name"], size))
        elif num_good:
            num_col = min(num_good, 6)
            keys = images.keys()
            keys.sort()
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == _RATING_GOOD:
                    links.append(self._GetRigLink(source_dir, entry["top_name"], -1))
        elif num_images:
            return self._GetRigLink(source_dir, None, None)

        if links:
            lines = []
            i = 0
            for link in links:
                if i % num_col == 0:
                    curr = []
                    lines.append(curr)
                curr.append(link)
                i += 1
            content = self._FillTemplate("image_table.html",
                                         theme=self._settings.theme,
                                         lines=lines)
            return content
        return None

    def _GetRigLink(self, source_dir, leafname, size):
        """
        Generates the URL to a rig image, with a caption, that links to the album.
        Size: Max pixel size or -1 for a thumbnail.
        
        If leafname & size are None, creates an URL to the album.
        
        TODO: site prefs (base url, size, title, thumbnail size, quality)
        """
        album_title = cgi.escape(os.path.basename(source_dir.rel_curr))
        album = urllib.quote(source_dir.rel_curr)
        link = self._settings.rig_url + 'index.php?album=' + album
        if leafname:
            title = os.path.splitext(leafname)[0]
            img = urllib.quote(leafname)
            img = '%sindex.php?th=&album=%s&img=%s&sz=%s&q=75' % (
                  self._settings.rig_url, album, img, size)
            content = '<img title="%(title)s" alt="%(title)s" src="%(img)s"/>' % {
                "title": title,
                "img": img }
        else:
            content = album_title
        url = '<a title="%(title)s" href="%(link)s">%(content)s</a>' % {
            "title": album_title,
            "link": link,
            "content": content }
        return url

    # Utilities, overridable for unit tests

    def _GetRating(self, ascii):
        return _RATING.get(ascii, _RATING_DEFAULT)

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

    def _ReadFile(self, full_path):
        """
        Returns the content of a file as a string.
        Will raise an IOError if the file cannot be read.
        """
        f = file(full_path)
        data = f.read()
        f.close()
        return data

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
        self._log.Info("[%s] Write %s", self._settings.public_name, dest_file)
        if not self._dry_run:
            f = file(dest_file, mode="wb")
            f.write(data)
            f.close()
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

    def _FillTemplate(self, template, **keywords):
        """
        Renders the given template with the given theme.
        Keywords are the special variables expected by the given template.
        Returns the generated HTML as a string.
        """
        assert "theme" in keywords
        template_file = os.path.join(self._TemplateDir(), keywords["theme"], template)
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
