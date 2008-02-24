#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "default" theme 

Site generators are instantiated by rig.site.__init__.py.CreateSite()

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
import operator
from datetime import date, datetime

from rig.site_base import SiteBase, SiteItem
from rig.template.template import Template
from rig.source_item import SourceDir, SourceFile
from rig.parser.dir_parser import RelFile
from rig.version import Version
from rig.sites_settings import SiteSettings

#------------------------
class SiteDefault(SiteBase):
    """
    Describes and how to generate the content of a site using the "default" theme.
    
    Right now the "magic" theme is identicaly to the "default" theme
    so the implementation is empty. This is expected to change later.
    """
    EXT_IZU = ".izu"
    EXT_HTML = ".html"
    INDEX_IZU = "index" + EXT_IZU
    INDEX_HTML = "index" + EXT_HTML
    _DATE_YMD = re.compile(r"^(?P<year>\d{4})[/-]?(?P<month>\d{2})[/-]?(?P<day>\d{2})"
                          r"(?:[ ,:/-]?(?P<hour>\d{2})[:/.-]?(?P<min>\d{2})(?:[:/.-]?(?P<sec>\d{2}))?)?"
                          r"(?P<rest>.*$)")
    _ITEMS_PER_PAGE = 20      # TODO make a site.rc pref
    _MANGLED_NAME_LENGTH = 50 # TODO make a site.rc pref
    
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
        """
        return self
        
    def GeneratePages(self, categories, items):
        """
        - categories: list of categories accumulated from each entry
        - items: list of SiteItem
        """
        # Sort by decreasing date (i.e. compares y to x, not x to y)
        items.sort(lambda x, y: cmp(y.date, x.date))

        # we skip categories if there's only one of them
        if len(categories) == 1:
            categories = []

        # Generate monthly pages and get a cached version of each item
        month_pages, cached_content = self._GenerateMonthPages("", "", None, categories, items)
        # Generate an index page with all posts (whether they have a category or not)
        self._GenerateIndexPage("", "", None, categories, items, month_pages, max_num_pages=1)

        # Only generate per-category months pages if we have more than one category
        if categories:
            for c in categories:
                month_pages, _ = self._GenerateMonthPages([ "cat", c ], "../../", [ c ],
                                               categories, items)
                self._GenerateIndexPage([ "cat", c ], "../../", [ c ],
                                                categories, items, month_pages, max_num_pages=1)

    def _GenerateIndexPage(self, path, rel_base,
                                category_filter, all_categories,
                                items, month_pages,
                                max_num_pages=None):
        """
        Generates most-recent pages with items that match the category_filter list.

        SiteItems are not re-ordered, it's up to the caller to order the items
        by decreasing date order.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper urls.
        - category_filter: list of categories to use for this page (acts as a filter)
            or None to accept all categories (even those with no categories)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Items MUST be sorted by decreasing date order.
        - month_pages: list(tuple(url, date)) for each month page generated for the
            same entries. Can be an empty list but not None. MUST be sorted in
            decreasing date order.
        - max_num_pages: How many pages of most-recent items? 0 or None to create them all.
        """
        base_url = "/".join(path)
        if base_url:
            base_url += "/"
        base_path = ""
        if path:
            base_path = os.path.join(*path)
            self._MkDestDir(base_path)

        # filter relevant items (or all of them if there's no category_filter)
        if category_filter is None:
            relevant_items = items
        else:
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
        if max_num_pages > 0:
            np = min(np, max_num_pages - 1)
        i = 0
        for p in xrange(0, np + 1):
            filename = "index%s.html" % (p > 0 and p or "")
            url = base_url + filename
            if p < np:
                next_url = base_url + "index%s.html" % (p + 1)
            else:
                next_url = None            

            keywords = self._settings.AsDict()
            keywords["title"] = "All Items"
            keywords["rel_base_url"] = rel_base
            keywords["prev_url"] = prev_url
            keywords["next_url"] = next_url
            keywords["curr_page"] = p + 1
            keywords["max_page"] = np + 1
            keywords["last_gen_ts"] = datetime.today()
            keywords["all_categories"] = all_categories
            keywords["month_pages"] = month_pages
            version = Version()
            keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                                  version.SvnRevision())

            entries = []
            older_date = None
            for j in relevant_items[i:i + self._ITEMS_PER_PAGE]:
                # SiteItem.content_gen is a lambda that generates the content
                entries.append(j.content_gen(keywords))
                older_date = (older_date is None) and j.date or max(older_date, j.date)
            i += self._ITEMS_PER_PAGE

            keywords["entries"] = entries
            keywords["last_content_ts"] = older_date
            
            content = self._FillTemplate("index.html", **keywords)
            self._WriteFile(content, self._settings.dest_dir, os.path.join(base_path, filename))
            prev_url = url

    def _GenerateMonthPages(self, path, rel_base,
                                category_filter, all_categories,
                                items, max_num_pages=None):
        """
        Generates months pages with items that match the category_filter list.
        
        SiteItems are not re-ordered, it's up to the caller to re-order the
        items by decreasing date order.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper urls.
        - category_filter: list of categories to use for this page (acts as a filter)
            or None to accept all categories (even those with no categories)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Items MUST be sorted by decreasing date order.
        - max_num_pages: How many pages to create? 0 or None to create them all.
        
        Returns:
        - a list( tuple(string: URL, date) ) of URLs to the pages just
          created with the date matching the month.
        - a dict( SiteItem: item => string: content) ) for each
          entry generated (where item is an item from the input items list).
        """
        result_urls = []
        result_entries = {}

        base_url = "/".join(path)
        if base_url:
            base_url += "/"
        base_path = ""
        if path:
            base_path = os.path.join(*path)
            self._MkDestDir(base_path)

        # filter relevant items (or all of them if there's no category_filter)
        if category_filter is None:
            relevant_items = items
        else:
            relevant_items = []
            for i in items:
                for c in i.categories:
                    if c in category_filter:
                        relevant_items.append(i)
                        break

        by_months = {}
        for i in relevant_items:
            # key is index=(year+month*16), the year and the month.
            # the index is there just to ease sorting.
            key = (i.date.year + i.date.month << 4, i.date.year, i.date.month)
            if not key in by_months:
                by_months[key] = []
            by_months[key].append(i)
        relevant_items = None
        keys = by_months.keys()
        keys.sort(reverse=True, key=operator.itemgetter(0))  # sort by key/index

        prev_url = None
        next_url = None
        np = len(keys)
        for n in xrange(0, np):
            month_key = keys[n]
            year = month_key[1]
            month = month_key[2]
            filename = self._MonthPageName(year, month)
            url = base_url + filename
            if n + 1 < np:
                next_url = base_url + self._MonthPageName(keys[n+1][1], keys[n+1][2])
            else:
                next_url = None

            keywords = self._settings.AsDict()
            keywords["title"] = "All Items"
            keywords["rel_base_url"] = rel_base
            keywords["prev_url"] = prev_url
            keywords["next_url"] = next_url
            keywords["curr_page"] = n + 1
            keywords["max_page"] = np + 1
            keywords["last_gen_ts"] = datetime.today()
            keywords["all_categories"] = all_categories
            version = Version()
            keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                                  version.SvnRevision())

            entries = []
            earlier_date = None
            older_date = None
            for j in by_months[month_key]:
                # SiteItem.content_gen is a lambda that generates the content
                content = j.content_gen(keywords)
                result_entries[j] = content
                entries.append(j.content_gen(keywords))
                older_date = (older_date is None) and j.date or max(older_date, j.date)
                earlier_date = (earlier_date is None) and j.date or min(earlier_date, j.date)
            if earlier_date is None:
                earlier_date = datetime(year, month, 1)

            keywords["entries"] = entries
            keywords["last_content_ts"] = older_date

            content = self._FillTemplate("month.html", **keywords)
            self._WriteFile(content, self._settings.dest_dir, os.path.join(base_path, filename))
            result_urls.append((url, earlier_date.date()))
            prev_url = url
        return result_urls, result_entries

    def _MonthPageName(self, year, month):
        return "%04d-%02d.html" % (year, month)
    
    def _Permalink(self, year, month, title):
        name = self._SimpleFileName(title)
        return "%s#%s" % (self._MonthPageName(year, month), name), name

    def GenerateItem(self, source_item):
        """
        Generates a new photoblog entry, which may have an index and/or may have an album.

        Returns a SiteItem that describes an entry for the site's pages.
        
        If the source item is not suitable (i.e. generates no data),
        the method must return None and the caller must be prepared to ignore it.

        Arguments:
        - source_item: An instance of SourceItem.
        """
        may_have_images = False
        all_files = None
        izu_file = None
        html_file = None

        if isinstance(source_item, SourceDir):
            rel_dir = source_item.rel_dir
            all_files = source_item.all_files
            may_have_images = True
            title = os.path.basename(rel_dir.rel_curr)
            if self.INDEX_IZU in all_files:
                izu_file = os.path.join(rel_dir.abs_path, self.INDEX_IZU)
                main_filename = RelFile(rel_dir.abs_path,
                                        os.path.join(rel_dir.rel_curr, self.INDEX_IZU))
            elif self.INDEX_HTML in all_files:
                html_file = os.path.join(rel_dir.abs_path, self.INDEX_HTML)
                main_filename = RelFile(rel_dir.abs_path,
                                        os.path.join(rel_dir.rel_curr, self.INDEX_HTML))

        elif isinstance(source_item, SourceFile):
            rel_file = source_item.rel_file
            title = os.path.basename(rel_file.rel_curr)
            main_filename = rel_file
            if rel_file.rel_curr.endswith(self.EXT_IZU):
                izu_file = rel_file.abs_path
                title = title[:-1 * len(self.EXT_IZU)]  # remove ext from title
            elif rel_file.rel_curr.endswith(self.EXT_HTML):
                html_file = rel_file.abs_path
                title = title[:-1 * len(self.EXT_HTML)]  # remove ext from title

        else:
            raise NotImplementedError("TODO support %s" % repr(source_item))
        
        date, title = self._DateAndTitleFromTitle(title)
        if not date:
            date = datetime.today()
        sections = {}
        tags = {}
        if izu_file:
            self._log.Info("[%s] Render '%s' to HTML", self._settings.public_name,
                           izu_file)
            tags, sections = self._izu_parser.RenderFileToHtml(izu_file)

            for s in sections.iterkeys():
                keywords = self._settings.AsDict()
                if may_have_images:
                    keywords["curr_album"] = urllib.quote(rel_dir.rel_curr)
                template = Template(self._log, source=sections[s])
                sections[s] = template.Generate(keywords)

        elif html_file:
            sections["html"] = self._ReadFile(html_file)
            tags = self._izu_parser.ParseFirstLine(sections["html"])
            self._log.Debug("HTML : %s => '%s'", main_filename, sections["html"])
        else:
            self._log.Debug("No content for source %s", source_item)
            return None

        # Are item categories accepted on this site?
        cats = tags.get("cat", {}).keys()
        if not self._AcceptCategories(cats, self._settings):
            return None
        cats.sort()

        date = tags.get("date", date)     # override directory's date
        title = tags.get("title", title)  # override directory's title

        img_params = None
        if may_have_images and not "images" in sections:
            img_params = { "rel_dir": rel_dir, "all_files":list(all_files) }

        keywords = self._settings.AsDict()
        keywords["title"] = title
        keywords["sections"] = dict(sections)
        keywords["date"] = date
        keywords["tags"] = dict(tags)
        keywords["categories"] = list(cats)
        permalink_url, permalink_name = self._Permalink(date.year, date.month, title)
        keywords["permalink_url"] = permalink_url
        keywords["permalink_name"] = permalink_name

        def _generate_content(_keywords, _img_params, _extra_keywords=None):
            # we need to make sure we can't contaminate the caller's dictionaries
            # so we just duplicate them here. Also we make sure not to use any
            # variables which are declared in the outer method.
            if _extra_keywords:
                temp = dict(_extra_keywords)
                temp.update(_keywords)
                _keywords = temp
            else:
                _keywords = dict(_keywords)

            if _img_params:
                html_img = self._GenerateImages(_img_params["rel_dir"], _img_params["all_files"])
                if html_img:
                    _keywords["sections"]["images"] = html_img
            return self._FillTemplate("entry.html", **_keywords)

        return SiteItem(date,
                        permalink_url,
                        categories=cats,
                        content_gen=lambda extra=None: _generate_content(keywords, img_params, extra))

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
        if not self._settings.rig_base:
            return None

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
        album = source_dir.rel_curr
        link = self._RigAlbumLink(self._settings, album)
        if leafname:
            title = os.path.splitext(leafname)[0]
            link = self._RigImgLink(self._settings, album, leafname)
            img = self._RigThumbLink(self._settings, album, leafname, size)
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

    def _RigAlbumLink(self, settings, album):
        if not settings.rig_base:
            return ""
        return settings.rig_album_url % {
                 "rig_base": settings.rig_base,
                 "album": urllib.quote(album) }

    def _RigImgLink(self, settings, album, img):
        if not settings.rig_base:
            return ""
        return settings.rig_img_url % {
                 "rig_base": settings.rig_base,
                 "album": urllib.quote(album),
                 "img":   urllib.quote(img) }

    def _RigThumbLink(self, settings, album, img, size):
        if not settings.rig_base:
            return ""
        return settings.rig_thumb_url % {
                 "rig_base": settings.rig_base,
                 "album": urllib.quote(album),
                 "img":   urllib.quote(img),
                 "size":  urllib.quote(str(size)) }

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
        template_file = self._TemplatePath(path=template, **keywords)
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
        if not m:
            return (None, title)
        try:
            return (datetime(int(m.group("year" ) or 0),
                             int(m.group("month") or 0),
                             int(m.group("day"  ) or 0),
                             int(m.group("hour" ) or 0),
                             int(m.group("min"  ) or 0),
                             int(m.group("sec"  ) or 0)),
                    (m.group("rest") or "").strip().strip("_"))
        except ValueError, e:
            self._log.Warn("Failed to extract date from title '%s': %s", title, str(e))
        
        # Fall back, trying again without the time part
        try:
            return (datetime(int(m.group("year" ) or 0),
                             int(m.group("month") or 0),
                             int(m.group("day"  ) or 0),
                             0,
                             0,
                             0),
                    (m.group("rest") or "").strip().strip("_"))
        except ValueError, e:
            # This time we don't ignore it. If you get an exception here, please
            # this your title or adjust the regexps for your site.
            self._log.Exception("Failed to extract date from title '%s': %s", title, str(e))
            raise

    def _AcceptCategories(self, cats, _settings):
        """
        This applies the category filters (includes & excludes) from the site's settings
        to the given list of categories of a given post.
        
        Parameters:
        - cats(list): A list of tag. List can be empty but not None.
        - settings(SiteSettings): A site's settings. Only cat_include and cat_exclude matter.

        Exclusions are matched using a "OR". Inclusions are matched using a "OR" too.
        
        Returns true if the post should be accepted, and false if the post should
        be filtered out.
        """
        # First apply exclusions... the first match makes the test fail
        exc = _settings.cat_exclude
        if exc == SiteSettings.CAT_ALL:
            return False  # everything is excluded
        elif exc:
            if not cats and SiteSettings.CAT_NOTAG in exc:
                return False  # exclude posts with no tags
            for cat in cats:
                if cat in exc:
                    return False  # some word is excluded

        # Then process inclusions... one of them must be there.
        inc = _settings.cat_include
        if not inc:
            return True  # default is to match everything
        if not cats and SiteSettings.CAT_NOTAG in inc:
            return True  # include posts with no tags
        for cat in cats:
            if cat in inc:
                return True  # some word is included
        return False  # no inclusion worked

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
