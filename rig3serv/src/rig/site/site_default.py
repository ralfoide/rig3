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
import zlib
import errno
import urllib
from datetime import datetime

from rig.site_base import SiteBase, SiteItem
from rig.template.template import Template
from rig.source_item import SourceDir
from rig.version import Version

#------------------------
class SiteDefault(SiteBase):
    """
    Describes on site and what we can do with it.
    """
    INDEX_IZU = "index.izu"
    INDEX_HTML = "index.html"
    _DATE_YMD = re.compile(r"^(?P<year>\d{4})[/-]?(?P<month>\d{2})[/-]?(?P<day>\d{2})"
                          r"(?:[ ,:/-]?(?P<hour>\d{2})[:/.-]?(?P<min>\d{2})(?:[:/.-]?(?P<sec>\d{2}))?)?"
                          r"(?P<rest>.*$)")
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

    def __init__(self, log, dry_run, settings):
        super(SiteDefault, self).__init__(log, dry_run, settings)

    def MakeDestDirs(self):
        """
        Creates the necessary directories in the destination.

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        
        Returns self for chaining

        Subclassing: Derived classes SHOULD override this. Parent does nothing.
        """
        self._MkDestDir(self._ITEMS_DIR)
        return self
        
    def GeneratePages(self, categories, items):
        """
        - categories: list of categories accumulated from each entry
        - items: list of SiteItem

        Subclassing: Derived classes MUST override this and not call the parent.
        """
        # Sort by decreasing date (i.e. compares y to x, not x to y)
        items.sort(lambda x, y: cmp(y.date, x.date))

        self._GeneratePageByCategory("", "", categories, categories, items)
        for c in categories:
            self._GeneratePageByCategory([ "cat", c ], "../../", [ c ], categories, items)
        # TODO: self.GeneratePageMonth(month, items)

    def _GeneratePageByCategory(self, path, rel_base, category_filter, all_categories, items):
        """
        Generates pages with items which have at least one category in the
        category_filter list. SiteItems are not re-ordered, it's up to the caller to
        re-order the items list if necessary.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper index.html urls.
        - category_filter: list of categories to use for this page (acts as a filter)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Only uses those which have at least one category
            in the category_filter list.
        """
        base_url = "/".join(path)
        if base_url:
            base_url += "/"
        base_path = ""
        if path:
            base_path = os.path.join(*path)
            self._MkDestDir(base_path)

        # filter relevant items
        relevant_items = []
        for i in items:
            for c in i.categories:
                if c in category_filter:
                    relevant_items.append(i)
                    break

        prev_url = None
        next_url = None
        n = len(relevant_items)
        np = n / self._ITEMS_PER_PAGE
        i = 0
        for p in xrange(0, np + 1):
            filename = "index%s.html" % (p > 0 and p or "")
            url = base_url + filename
            if p < np:
                next_url = base_url + "index%s.html" % (p + 1)
            else:
                next_url = None            
            entries = []
            older_date = None
            for j in relevant_items[i:i + self._ITEMS_PER_PAGE]:
                entries.append(j.content)
                older_date = (older_date is None) and j.date or max(older_date, j.date)
            i += self._ITEMS_PER_PAGE

            keywords = self._settings.AsDict()
            keywords["title"] = "All Items"
            keywords["entries"] = entries
            keywords["rel_base_url"] = rel_base
            keywords["prev_url"] = prev_url
            keywords["next_url"] = next_url
            keywords["curr_page"] = p + 1
            keywords["max_page"] = np + 1
            keywords["last_gen_ts"] = datetime.today()
            keywords["last_content_ts"] = older_date
            keywords["all_categories"] = all_categories
            version = Version()
            keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                                  version.SvnRevision())
            
            content = self._FillTemplate("index.html", **keywords)
            self._WriteFile(content, self._settings.dest_dir, os.path.join(base_path, filename))
            prev_url = url

    def GenerateItem(self, source_item):
        """
        Generates a new photoblog entry, which may have an index and/or may have an album.
        Returns an SiteItem or None

        Arguments:
        - source_item: An instance of SourceItem.

        Subclassing: Derived classes MUST override this and not call the parent.
        """
        if isinstance(source_item, SourceDir):
            source_dir = source_item.source_dir
            all_files = source_item.all_files
        else:
            raise NotImplementedError("TODO support %s" % repr(source_item))
        
        title = os.path.basename(source_dir.rel_curr)
        date, title = self._DateAndTitleFromTitle(title)
        if not date:
            date = datetime.today()
        main_filename = ""
        sections = {}
        tags = {}
        if self.INDEX_IZU in all_files:
            main_filename = self.INDEX_IZU
            izu_file = os.path.join(source_dir.abs_dir, self.INDEX_IZU)
            self._log.Info("[%s] Render '%s' to HMTL", self._settings.public_name,
                           izu_file)
            tags, sections = self._izu_parser.RenderFileToHtml(izu_file)

            album = urllib.quote(source_dir.rel_curr)
            keywords = { "rig_curr_album_link":
                            self._settings.rig_url + 'index.php?album=' + album }
            for s in sections.iterkeys():
                template = Template(self._log, source=sections[s])
                sections[s] = template.Generate(keywords)

        elif self.INDEX_HTML in all_files:
            main_filename = self.INDEX_HTML
            html_file = os.path.join(source_dir.abs_dir, self.INDEX_HTML)
            sections["html"] = self._ReadFile(html_file)
            tags = self._izu_parser.ParseFirstLine(sections["html"])
            self._log.Debug("HTML : %s => '%s'", main_filename, sections["html"])
        else:
            self._log.Debug("No content for source %s", source_dir)
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
        if self._TEMPLATE_NEED_ITEM_FILES:
            assert self._WriteFile(content,
                                   os.path.join(self._settings.dest_dir, self._ITEMS_DIR),
                                   filename)
        dest = os.path.join(self._ITEMS_DIR, filename)
        return SiteItem(date, dest, content=content, categories=cats)

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
        num_normal = 0 
        for filename in all_files:
            m = self._IMG_PATTERN.match(filename)
            if m:
                num_images += 1
                index = m.group("index")
                entry = images[index] = images.get(index, { "top_rating": self._RATING_BASE, "top_name": None, "files": [] })
                rating = self._GetRating(m.group("rating"))
                num_normal += (rating == self._RATING_DEFAULT and 1 or 0)
                num_good += (rating == self._RATING_GOOD and 1 or 0)
                num_excellent += (rating == self._RATING_EXCELLENT and 1 or 0)
                if rating > entry["top_rating"]:
                    entry["top_rating"] = rating
                    entry["top_name"] = filename
                entry["files"].append(filename)
        
        links = []
        if num_excellent:
            size = 400
            if num_excellent > 2:
                size = max(300, 800 / num_excellent)
            num_col = min(num_excellent, 4)
            keys = images.keys()
            keys.sort()
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == self._RATING_EXCELLENT:
                    links.append(self._GetRigLink(source_dir, entry["top_name"], size))
        elif num_good:
            num_col = min(num_good, 6)
            keys = images.keys()
            keys.sort()
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == self._RATING_GOOD:
                    links.append(self._GetRigLink(source_dir, entry["top_name"], -1))
        elif num_normal > 0 and num_normal <= 6:  # TODO: max_num_normal site pref
            num_col = num_normal
            keys = images.keys()
            keys.sort()
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == self._RATING_DEFAULT:
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
        Generates the URL to a rig image, with a caption, that links to the given image
        (or the album if there's no image).
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
            link += '&img=' + img
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
        return self._RATING.get(ascii, self._RATING_DEFAULT)

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

    def _DateAndTitleFromTitle(self, title):
        """
        Parses the a title and extract a date and the real title.
        Returns:
        - a tuple (datetime, title)
        - or (None, original title)
        """
        m = self._DATE_YMD.match(title)
        if m:
            return (datetime(int(m.group("year" ) or 0),
                             int(m.group("month") or 0),
                             int(m.group("day"  ) or 0),
                             int(m.group("hour" ) or 0),
                             int(m.group("min"  ) or 0),
                             int(m.group("sec"  ) or 0)),
                    (m.group("rest") or "").strip().strip("_"))
        return (None, title)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
