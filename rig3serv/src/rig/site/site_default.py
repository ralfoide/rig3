#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "default" theme

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = "ralfoide at gmail com"

import re
import os
import cgi
import zlib
import time
import urllib
from datetime import date, datetime

from rig.parser.izu_parser import IzuParser
from rig.site_base import SiteBase, SiteItem
from rig.template.template import Template
from rig.source_item import SourceDir, SourceFile
from rig.parser.dir_parser import RelPath, PathTimestamp
from rig.version import Version
from rig.sites_settings import DEFAULT_ITEMS_PER_PAGE
from rig.cache import Cache
from rig.hash_store import HashStore

#------------------------
class ContentEntry(object):
    def __init__(self, content, title, date, permalink):
        self.content = content
        self.title = title
        self.date = date
        self.permalink = permalink

    def __repr__(self):
        return "<%s: title %s, date %s, link %s, content %s>" % (
             self.__class__.__name__, self.title, self.date, self.permalink, self.content)

#------------------------
class MonthPageItem(object):
    def __init__(self, url, date):
        self.url = url
        self.date = date

    def __repr__(self):
        return "<%s: url %s, date %s>" % (self.__class__.__name__, self.url, self.date)

#------------------------
class SiteDefault(SiteBase):
    """
    Describes how to generate the content of a site using the "default" theme.

    Right now the "magic" theme is identical to the "default" theme
    so the implementation is empty. This is expected to change later.
    """
    EXT_IZU = ".izu"
    EXT_HTML = ".html"
    INDEX_IZU = "index" + EXT_IZU
    INDEX_HTML = "index" + EXT_HTML

    # This can be overridden by SiteSetting.date_ymd_pattern
    _DATE_YMD = re.compile(r"^(?P<year>\d{4})[/-]?(?P<month>\d{2})[/-]?(?P<day>\d{2})?"
                          r"(?:[ ,:/-]?(?P<hour>\d{2})[:/.-]?(?P<min>\d{2})(?:[:/.-]?(?P<sec>\d{2}))?)?"
                          r"(?P<rest>.*$)")

    # This can be overridden by SiteSetting.img_pattern
    _IMG_PATTERN = re.compile(r"^(?P<index>[A-Z]{0,2}\d{2,})(?P<rating>[ \._+=-])(?P<name>.+?)"
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

    _TEMPLATE_HTML_INDEX   = "html_index.html"    # template for main HTML page
    _TEMPLATE_HTML_MONTH   = "html_month.html"    # template for month HTML page
    _TEMPLATE_HTML_ENTRY   = "html_entry.html"    # template for individual entries in HTML page
    _TEMPLATE_HTML_TOC     = "html_toc.html"      # template for HTML TOC
    _TEMPLATE_ATOM_FEED    = "atom_feed.xml"      # template for atom feed
    _TEMPLATE_ATOM_ENTRY   = "atom_entry.xml"     # template for individual entries in atom feed
    _TEMPLATE_ATOM_CONTENT = "atom_content.xml"   # template for content of atom entry
    _TEMPLATE_IMG_TABLE    = "image_table.html"   # template for image table in HTML


    def __init__(self, log, dry_run, force, site_settings):
        super(SiteDefault, self).__init__(log, dry_run, force, site_settings)
        self._last_gen_ts = datetime.today()

        # Customize the cache directory by hashing the site's public name in it.
        # This makes the cache site-specific for people who still want to have
        # just one global cache_dir in their config file.
        self._cache = Cache(log, site_settings.cache_dir)
        self._cache.SetCacheDir(
                os.path.join(site_settings.cache_dir,
                             self._cache.GetKey(site_settings.public_name)))

        self._hash_store = HashStore(log, self._cache)

        self._enable_cache = os.getenv("DISABLE_RIG3_CACHE") is None
        self._debug_cache  = os.getenv("DEBUG_RIG3_CACHE")   is not None

        if self._enable_cache:
            self._hash_store.Load()
            self._ClearCache(site_settings)
        else:
            self._log.Info("[%s] Cache is disabled.",
                           self._site_settings.public_name)

    def Dispose(self):
        if self._enable_cache:
            self._hash_store.Save()
            self._cache.DisplayCounters(self._log)
        super(SiteDefault, self).Dispose()

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
        Generates several pages:
        - Index page (max N last entries)
        - Month pages (all entries per month)
        - Categorie pages (all entries per category)

        Input:
        - categories: list of categories accumulated from each entry
        - items: list of SiteItem
        """
        # Sort by decreasing date (i.e. compares y to x, not x to y)
        items.sort(lambda x, y: cmp(y.date, x.date))

        # we skip categories if there's only one of them
        if len(categories) == 1:
            categories = []

        # Do we have to generate anything at all?
        hash_key = self._cache.GetKey([ categories, items ])

        if self._hash_store.Contains(hash_key):
            if self._force:
                self._log.Info("[%s] No new content found, forcing generation",
                               self._site_settings.public_name)
            else:
                self._log.Info("[%s] No new content found, skipping generation",
                               self._site_settings.public_name)
                return

        # Generate monthly pages and get a cached version of each item
        month_pages = self._GenerateMonthPages("", "", None, categories, items)
        # Generate an index page with all posts (whether they have a category or not)
        self._GenerateIndexPage("", "", None, categories, items, month_pages)
        self._GenerateAtomFeed ("", "", None, categories, items, month_pages)

        # Only generate per-category months pages if we have more than one category
        if categories:
            for c in categories:
                month_pages = self._GenerateMonthPages([ "cat", c ], "../../", c,
                                               categories, items)
                self._GenerateIndexPage([ "cat", c ], "../../", c,
                                        categories, items, month_pages)
                self._GenerateAtomFeed ([ "cat", c ], "../../", c,
                                        categories, items, month_pages)

        self._hash_store.Add(hash_key)

    def _GenerateIndexPage(self, path, rel_base,
                                curr_category, all_categories,
                                items, month_pages,
                                base_filename="index"):
        """
        Generates most-recent pages with items that match the curr_category.

        SiteItems are not re-ordered, it's up to the caller to order the items
        by decreasing date order.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper urls.
        - curr_category: current category to use for this page (acts as a filter)
            or None to accept all categories (even those with no categories)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Items MUST be sorted by decreasing date order.
        - month_pages: list(MonthPageItem(url, date)) for each month page generated for the
            same entries. Can be an empty list but not None. MUST be sorted in
            decreasing date order.
        - base_filename: If you want to generate something else than indexNN.html files.
        """
        base_url = "/".join(path)
        if base_url:
            base_url += "/"
        base_path = ""
        if path:
            base_path = os.path.join(*path)
            self._MkDestDir(base_path)

        # filter relevant items (or all of them if there's no curr_category)
        if curr_category is None:
            relevant_items = items
        else:
            relevant_items = []
            for i in items:
                for c in i.categories:
                    if c == curr_category:
                        relevant_items.append(i)
                        break

        if curr_category in self._site_settings.reverse_categories:
            # sort by increasing date (thus reverse the name "decreasing date" order)
            relevant_items.sort(lambda x, y: cmp(x.date, y.date))

        num_item_page = self._site_settings.num_item_page
        assert isinstance(num_item_page, (int, long))
        if num_item_page < 1:
            num_item_page = DEFAULT_ITEMS_PER_PAGE

        keywords = self._site_settings.AsDict()

        if curr_category:
            title = curr_category.capitalize()
        else:
            title = "All Items"
        keywords["title"] = title

        keywords["curr_url"] = keywords.get("base_url", "") + base_url
        keywords["rel_base_url"] = rel_base
        keywords["last_gen_ts"] = self._last_gen_ts
        keywords["all_categories"] = all_categories
        keywords["curr_category"] = curr_category
        keywords["toc_categories"] = self._site_settings.toc_categories.Filter(all_categories)
        keywords["month_pages"] = month_pages
        keywords["html_toc"] = SiteDefault._TEMPLATE_HTML_TOC
        version = Version()
        keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                              version.SvnRevision())

        use_curr_month_in_index = self._site_settings.use_curr_month_in_index
        all_entries = []
        entries = []
        older_date = None
        n = len(relevant_items)
        if n > 0:
            curr_month = self._GetMonth(relevant_items[0].date)
            is_first_page = True

            for j in relevant_items:
                # SiteItem.content_gen is a lambda that generates the content
                content = j.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY, keywords)
                entry = ContentEntry(content, j.title, j.date, j.permalink)
                all_entries.append(entry)

                entry_month = self._GetMonth(j.date)

                if is_first_page:
                    is_first_page = (entry_month == curr_month and use_curr_month_in_index) \
                                     or (len(entries) < num_item_page)

                if is_first_page:
                    entries.append(entry)
                    older_date = (older_date is None) and j.date or max(older_date, j.date)

        filename = "%s.html" % base_filename
        keywords["all_entries"] = all_entries
        keywords["entries"] = entries
        keywords["last_content_ts"] = older_date

        content = self._FillTemplate(SiteDefault._TEMPLATE_HTML_INDEX, **keywords)
        self._WriteFile(content, self._site_settings.dest_dir, os.path.join(base_path, filename))

    def _GenerateAtomFeed(self, path, rel_base,
                                curr_category, all_categories,
                                items, month_pages):
        """
        Generates atom feed with most-recent items which match the curr_category.

        SiteItems are not re-ordered, it's up to the caller to order the items
        by decreasing date order.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper urls.
        - curr_category: current category to use for this page (acts as a filter)
            or None to accept all categories (even those with no categories)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Items MUST be sorted by decreasing date order.
        - month_pages: list(MonthPageItem(url, date)) for each month page generated for the
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

        # filter relevant items (or all of them if there's no curr_category)
        if curr_category is None:
            relevant_items = items
        else:
            relevant_items = []
            for i in items:
                for c in i.categories:
                    if c == curr_category:
                        relevant_items.append(i)
                        break

        if self._site_settings.num_item_atom > 0:
            relevant_items = relevant_items[:self._site_settings.num_item_atom]

        filename = "atom.xml"

        keywords = self._site_settings.AsDict()

        curr_url = keywords.get("base_url", "") + base_url
        keywords["curr_url"] = curr_url

        if curr_category:
            title = curr_category.capitalize()
        else:
            title = "All Items"
        keywords["title"] = title

        keywords["rel_base_url"] = rel_base
        keywords["last_gen_ts"] = self._last_gen_ts
        keywords["month_pages"] = month_pages
        keywords["all_categories"] = all_categories
        keywords["curr_category"] = curr_category
        version = Version()
        keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                              version.SvnRevision())


        entries = []
        older_date = None
        for i in relevant_items:
            # Generate the content of the post first
            content = i.content_gen(SiteDefault._TEMPLATE_ATOM_CONTENT, keywords)
            keywords["atom_id"] = self._AtomId(curr_url, i.date, i.title)
            keywords["content"] = content
            # Then generate the <entry> for the post
            content = i.content_gen(SiteDefault._TEMPLATE_ATOM_ENTRY, keywords)
            entry = ContentEntry(content, i.title, i.date, i.permalink)
            entries.append(entry)
            older_date = (older_date is None) and i.date or max(older_date, i.date)

        keywords["entries"] = entries
        keywords["last_content_ts"] = older_date
        if older_date:
            keywords["last_content_iso"] = self._DateToIso(older_date)
        else:
            keywords["last_content_iso"] = self._DateToIso(self._last_gen_ts)

        # Finally generate the whole feed
        content = self._FillTemplate(SiteDefault._TEMPLATE_ATOM_FEED, **keywords)
        self._WriteFile(content, self._site_settings.dest_dir, os.path.join(base_path, filename))

    def _AtomId(self, curr_url, date, title):
        name = self._SimpleFileName(title)
        return "%s%04d-%02d/%s" % (curr_url,
                                     date.year, date.month,
                                     name)

    def _GenerateMonthPages(self, path, rel_base,
                                curr_category, all_categories,
                                items, max_num_pages=None):
        """
        Generates months pages with items that match the curr_category.

        SiteItems are not re-ordered, it's up to the caller to re-order the
        items by decreasing date order.

        - path: A list of sub-directories/sub-path indicating where the files are
            being created. If the list is empty, the files will be created in the root.
            This is used also to generate the proper urls.
        - curr_category: current category to use for this page (acts as a filter)
            or None to accept all categories (even those with no categories)
        - all_categories: list of all categories (used for template to create links)
        - items: list of SiteItem. Items MUST be sorted by decreasing date order.
        - max_num_pages: How many pages to create? 0 or None to create them all.

        Returns a list( MonthPageItem(string: URL, date) ) of URLs to the pages just
        created with the date matching the month.
        """
        month_pages = []

        base_url = "/".join(path)
        if base_url:
            base_url += "/"
        base_path = ""
        if path:
            base_path = os.path.join(*path)
            self._MkDestDir(base_path)

        # filter relevant items (or all of them if there's no curr_category)
        if curr_category is None:
            relevant_items = items
        else:
            relevant_items = []
            for i in items:
                for c in i.categories:
                    if c == curr_category:
                        relevant_items.append(i)
                        break

        if curr_category in self._site_settings.reverse_categories:
            # sort by increasing date (thus reverse the name "decreaseing date" order)
            relevant_items.sort(lambda x, y: cmp(x.date, y.date))

        by_months = {}
        for i in relevant_items:
            # key is date(year, month), the year and the month.
            # the index is there just to ease sorting.
            key = self._GetMonth(i.date)
            if not key in by_months:
                by_months[key] = []
            by_months[key].append(i)
        relevant_items = None
        keys = by_months.keys()

        # The "natural" sort is to do a reverse sort.
        # If this category is reversed, use an incrementing sort.
        keys.sort(reverse=not curr_category in self._site_settings.reverse_categories)

        np = len(keys)
        for n in xrange(0, np):
            month_key = keys[n]
            year = month_key.year
            month = month_key.month
            filename = self._MonthPageName(year, month)
            month_pages.append(MonthPageItem(filename, month_key))

        keywords = self._site_settings.AsDict()

        if curr_category:
            title = curr_category.capitalize()
        else:
            title = "All Items"
        keywords["title"] = title

        keywords["curr_url"] = keywords.get("base_url", "") + base_url
        keywords["rel_base_url"] = rel_base
        keywords["last_gen_ts"] = self._last_gen_ts
        keywords["all_categories"] = all_categories
        keywords["curr_category"] = curr_category
        keywords["toc_categories"] = self._site_settings.toc_categories.Filter(all_categories)
        keywords["month_pages"] = month_pages
        keywords["html_toc"] = SiteDefault._TEMPLATE_HTML_TOC
        version = Version()
        keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                              version.SvnRevision())

        pages = []
        all_entries = []

        for p in month_pages:
            filename = p.url
            month_key = p.date

            entries = []
            older_date = None
            for j in by_months[month_key]:
                # SiteItem.content_gen is a lambda that generates the content
                content = j.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY, keywords)
                entry = ContentEntry(content, j.title, j.date, j.permalink)
                entries.append(entry)
                all_entries.append(entry)
                older_date = (older_date is None) and j.date or max(older_date, j.date)
            pages.append((p, filename, entries, older_date))

        keywords["all_entries"] = all_entries

        for page in pages:
            p = page[0]
            filename = page[1]
            keywords["entries"] = page[2]
            keywords["last_content_ts"] = page[3]
            keywords["title"] = title + " - " + p.date.strftime("%B %Y")

            content = self._FillTemplate(SiteDefault._TEMPLATE_HTML_MONTH, **keywords)
            self._WriteFile(content, self._site_settings.dest_dir, os.path.join(base_path, filename))

        return month_pages

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
        may_have_images, all_files, izu_file, html_file, title, rel_dir = \
                                            self.__GenItem_GetFiles(source_item)

        # TODO keep 2 keyword dicts: the main site_settings which does NOT
        # need to be hashed for the cache (cache gets cleared on settings)
        # and a 2nd keyword local for here. Pre-Hash the 2nd then merge
        # then in the 2-gen methods hash the _extra_keywords separately
        keywords = self._site_settings.AsDict()
        keywords.update(source_item.source_settings.AsDict())

        section_args = [ source_item,
                         may_have_images,
                         izu_file,
                         html_file,
                         rel_dir,
                         keywords ]

        sections, tags = self._cache.Compute(
                 section_args,
                 lambda: self.__GenItem_GetSections(*section_args),
                 stat_prefix="1.1 Izu",
                 use_cache=self._enable_cache)

        if sections is None:
            return None

        # Are item categories accepted on this site?
        cats = tags.get("cat", {}).keys()
        if not self._site_settings.cat_filter.Matches(cats):
            return None
        cats.sort()

        return self.__GenItem_CreateSiteItem(source_item,
                                             may_have_images,
                                             all_files,
                                             rel_dir,
                                             keywords,
                                             sections,
                                             tags,
                                             cats,
                                             title)

    def __GenItem_GetFiles(self, source_item):
        may_have_images = False
        all_files = None
        izu_file = None
        html_file = None
        rel_dir = None

        if isinstance(source_item, SourceDir):
            rel_dir = source_item.rel_dir
            all_files = source_item.all_files
            may_have_images = True
            title = rel_dir.basename()
            if self.INDEX_IZU in all_files:
                izu_file = rel_dir.join(self.INDEX_IZU)
            elif self.INDEX_HTML in all_files:
                html_file = rel_dir.join(self.INDEX_HTML)

        elif isinstance(source_item, SourceFile):
            rel_file = source_item.rel_file
            title = rel_file.basename()
            if rel_file.rel_curr.endswith(self.EXT_IZU):
                izu_file = rel_file
                title = title[:-1 * len(self.EXT_IZU)]  # remove ext from title
            elif rel_file.rel_curr.endswith(self.EXT_HTML):
                html_file = rel_file
                title = title[:-1 * len(self.EXT_HTML)]  # remove ext from title

        else:
            raise NotImplementedError("TODO support %s" % repr(source_item))

        return may_have_images, all_files, izu_file, html_file, title, rel_dir

    def __GenItem_GetSections(self,
                              source_item,
                              may_have_images,
                              izu_file,
                              html_file,
                              rel_dir,
                              keywords):
        sections = {}
        tags = {}

        if izu_file:
            self._log.Info("[%s] Render '%s' to HTML",
                           self._site_settings.public_name,
                           izu_file)

            p = IzuParser(self._log,
                              keywords["rig_base"],
                              keywords["img_gen_script"])
            tags, sections = p.RenderFileToHtml(izu_file)

            for k, v in sections.iteritems():
                if isinstance(v, (str, unicode)):
                    if may_have_images:
                        keywords["curr_album"] = urllib.quote(rel_dir.rel_curr)
                    template = Template(self._log, source=v)
                    sections[k] = template.Generate(keywords)
                elif k == "images":
                    if may_have_images:
                        keywords["curr_album"] = urllib.quote(rel_dir.rel_curr)
                        keywords["lines"] = [v]  # one line of many columns
                        content = self._FillTemplate(SiteDefault._TEMPLATE_IMG_TABLE, **keywords)
                        template = Template(self._log, source=content)
                        sections[k] = template.Generate(keywords)
                    else:
                        sections[k] = ""

        elif html_file:
            sections["html"] = self._ReadFile(html_file)
            izu_parser = IzuParser(self._log,
                                   keywords["rig_base"],
                                   keywords["img_gen_script"])
            tags = izu_parser.ParseFirstLine(sections["html"])
            #DEBUG--self._log.Debug("HTML : %s => '%s'", main_filename, sections["html"])
        else:
            self._log.Debug("No content for source %s", source_item)
            return None, None

        return sections, tags

    def __GenItem_CreateSiteItem(self,
                                 source_item,
                                 may_have_images,
                                 all_files,
                                 rel_dir,
                                 keywords,
                                 sections,
                                 tags,
                                 cats,
                                 title):
        # TODO split here
        date, title = self._DateAndTitleFromTitle(title)
        if not date:
            date = self._last_gen_ts
        date = tags.get("date", date)     # override directory's date
        title = tags.get("title", title)  # override directory's title

        img_params = None
        if may_have_images and not "images" in sections:
            img_params = { "rel_dir": rel_dir, "all_files":list(all_files) }

        keywords["title"] = title
        keywords["sections"] = dict(sections)
        keywords["date"] = date
        keywords["date_iso"] = self._DateToIso(date)
        keywords["tags"] = dict(tags)
        keywords["categories"] = list(cats)
        permalink_url, permalink_name = self._Permalink(date.year, date.month, title)
        keywords["permalink_url"] = permalink_url
        keywords["permalink_name"] = permalink_name
        keywords["_cache_key"] = self._cache.GetKey(keywords)

        return SiteItem(source_item,
                        date,
                        title,
                        permalink_url,
                        categories=cats,
                        content_gen=lambda template, extra=None: \
                            self.__GenItem_GenContent(template, keywords, img_params, extra))

    def __GenItem_GenContent(self, _template, _keywords, _img_params, _extra_keywords=None):
        # we need to make sure we can't contaminate the caller's dictionaries
        # so we just duplicate them here. Also we make sure not to use any
        # variables which are declared in the outer method.
        if _extra_keywords:
            _temp = dict(_extra_keywords)
            _temp.update(_keywords)
            _keywords = _temp
        else:
            _keywords = dict(_keywords)

        if _img_params:
            _html_img = self._GenerateImages(_img_params["rel_dir"],
                                             _img_params["all_files"],
                                             _keywords)
            if _html_img:
                _keywords["sections"]["images"] = _html_img

        _cache_key = [ _template, _keywords["_cache_key"] ]
        if _extra_keywords:
            _key_temp_dict = _extra_keywords.copy()
            # invalidate some timestamps that changes at every run
            _key_temp_dict["last_gen_ts"] = None
            _key_temp_dict["last_content_iso"] = None
            _cache_key.append(_key_temp_dict)

        _content = self._cache.Compute(
               _cache_key,
               lambda: self._FillTemplate(_template, **_keywords),
               stat_prefix="2.2 Content",
               use_cache=self._enable_cache)

        return _content

    def _GenerateImages(self, source_dir, all_files, keywords):
        """
        Generates a table with images.

        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        - all_files: List of "interesting/acceptable" files in the directory.
        - keywords: SiteItem keywords (e.g. specific to current blog entry)

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
        rig_base = keywords["rig_base"]
        if not rig_base:
            self._log.Info("[%s], No rig_base, no images generated for %s",
                           self._site_settings.public_name,
                           source_dir.rel_curr)
            return None

        img_pattern = None
        if keywords:
            img_pattern = keywords.get("img_pattern")
        if not img_pattern:
            img_pattern = self._IMG_PATTERN

        images = {}
        # images: index => { "top_rating": number,
        #                    "files": [ pattern.groupdict + "full": leaf name ] }
        num_excellent = 0
        num_good = 0
        num_images = 0
        num_normal = 0
        for filename in all_files:
            m = img_pattern.match(filename)
            if m:
                num_images += 1
                index = m.group("index")
                entry = images[index] = images.get(index,
                                                   { "top_rating": self._RATING_BASE,
                                                     "top_name": None,
                                                     "files": [],
                                                     "ts": [] })
                rating = self._GetRating(m.group("rating"))
                num_normal += (rating == self._RATING_DEFAULT and 1 or 0)
                num_good += (rating == self._RATING_GOOD and 1 or 0)
                num_excellent += (rating == self._RATING_EXCELLENT and 1 or 0)
                if rating > entry["top_rating"]:
                    entry["top_rating"] = rating
                    entry["top_name"] = filename
                entry["files"].append(filename)
                entry["ts"].append(PathTimestamp(os.path.join(source_dir.realpath(),
                                                              filename)))

        nums = (num_excellent, num_good, num_images, num_normal)

        cache_key = [ source_dir,
                      all_files,
                      images,
                      keywords.get("_cache_key", None) ]

        c = self._cache.Compute(
                    key=cache_key,
                    lambda_expr=lambda : self.__GenImage_CreateHtml(source_dir, nums, images, keywords),
                    stat_prefix="2.1 Images",
                    use_cache=self._enable_cache)
        return c

    def __GenImage_CreateHtml(self, source_dir, nums, images, keywords):
        # TODO: the heuristics below are lousy. Works for me, and even that
        # is questionable and all these constants... pfff. Need something
        # better. Maybe some inline-python mini-rules in the prefs?

        num_excellent, num_good, num_images, num_normal = nums
        series = []
        if num_excellent or num_good:

            if num_excellent:
                # We got some excellent-rated images.
                # Display them all with large previews with a max size ranging
                # from 300 to 800px depending on the number of images.
                size = 400
                if num_excellent > 2:
                    size = max(300, 800 / num_excellent)
                keys = images.keys()
                keys.sort()
                links = []
                for key in keys:
                    entry = images[key]
                    if entry["top_rating"] == self._RATING_EXCELLENT:
                        links.append(self._GetRigLink(keywords, source_dir, entry["top_name"], size))
                series.append(links)

            if num_good:
                # We got some good-rated images. Put them under the excellent ones if any.
                # Display them all with large previews with a max size ranging
                # from 200 to 400px depending on the number of images.
                size = 300
                if num_good > 2:
                    size = max(200, 400 / num_good)
                keys = images.keys()
                keys.sort()
                merge_in_excellent = len(series) > 0 and (num_excellent == 1 or num_good == 1)
                if merge_in_excellent:
                    links = series[0]
                else:
                    links = []
                for key in keys:
                    entry = images[key]
                    if entry["top_rating"] == self._RATING_GOOD:
                        links.append(self._GetRigLink(keywords, source_dir, entry["top_name"], size))
                if not merge_in_excellent:
                    series.append(links)

        elif num_normal > 0 and num_normal <= 6:  # TODO: max_num_normal site pref
            # We got some up to 6 normal-rated images.
            # Display them using the default preview size.
            keys = images.keys()
            keys.sort()
            links = []
            for key in keys:
                entry = images[key]
                if entry["top_rating"] == self._RATING_DEFAULT:
                    links.append(self._GetRigLink(keywords, source_dir, entry["top_name"], -1))
            series.append(links)

        elif num_images:
            # There are some images but none is considered good enough for the
            # auto-preview. Just generate a link on the album.
            #
            # TODO: the static string should move to the HTML template.
            # TODO: it would make sense to display this even for the other cases
            #       if there were other images not shown.
            title = (keywords and "title" in keywords) and keywords["title"] or None
            return "See more images for " + self._GetRigLink(keywords, source_dir, None, None, title)

        if series:
            content = self._FillTemplate(SiteDefault._TEMPLATE_IMG_TABLE,
                                         theme=keywords["theme"],
                                         lines=series)
            return content
        return None

    def _GetRigLink(self, keywords, source_dir, leafname, size, title=None):
        """
        Generates the URL to a rig image, with a caption, that links to the given image
        (or the album if there's no image).
        Size: Max pixel size or -1 for a thumbnail.

        If title is not None, it is used as the album title or image tooltip.
        If title is None, leafname is used for the image tooltip and the
        directory name is used for the album title.

        If leafname & size are None, creates an URL to the album.

        TODO: site prefs (base url, size, title, thumbnail size, quality)
        """
        album_title = title or cgi.escape(os.path.basename(source_dir.rel_curr))
        album = source_dir.rel_curr
        link = self._RigAlbumLink(keywords, album)
        if leafname:
            tooltip = title or os.path.splitext(leafname)[0]
            link = self._RigImgLink(keywords, album, leafname)
            img = self._RigThumbLink(keywords, album, leafname, size)
            content = '<img title="%(title)s" alt="%(title)s" src="%(img)s"/>' % {
                "title": tooltip,
                "img": img }
        else:
            content = album_title
        html = '<a title="%(title)s" href="%(link)s">%(content)s</a>' % {
            "title": album_title,
            "link": link,
            "content": content }
        return html

    # Utilities, overridable for unit tests

    def _DateToIso(self, date):
        return datetime.utcfromtimestamp(time.mktime(time.gmtime(time.mktime( date.timetuple() )))).isoformat() + "Z"

    def _RigAlbumLink(self, keywords, album):
        if not keywords["rig_base"]:
            return ""
        k = dict(keywords)
        k["album"] = urllib.quote(album)
        return k["rig_album_url"] % k

    def _RigImgLink(self, keywords, album, img):
        if not keywords["rig_base"]:
            return ""
        k = dict(keywords)
        k["album"] = urllib.quote(album)
        k["img"] = urllib.quote(img)
        return k["rig_img_url"] % k

    def _RigThumbLink(self, keywords, album, img, size):
        if not keywords["rig_base"]:
            return ""
        k = dict(keywords)
        k["album"] = urllib.quote(album)
        k["img"] = urllib.quote(img)
        k["size"] = urllib.quote(str(size))
        return k["rig_thumb_url"] % k

    def _GetRating(self, ascii):
        return self._RATING.get(ascii, self._RATING_DEFAULT)

    def _ReadFile(self, full_path):
        """
        Returns the content of a file as a string.
        Will raise an IOError if the file cannot be read.
        """
        if isinstance(full_path, RelPath):
            full_path = full_path.abs_path

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
        if self._dry_run:
            self._log.Info("[%s] (Dry-Run) Would write %s",
                           self._site_settings.public_name,
                           dest_file)
        else:
            self._log.Info("[%s] Write %s",
                           self._site_settings.public_name,
                           dest_file)
            f = file(dest_file, mode="wb")
            f.write(data)
            f.close()
        return dest_file

    def _SimpleFileName(self, leafname, maxlen=0):
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
        if maxlen <= 0:
            maxlen = self._site_settings.mangled_name_len
        if maxlen > 0 and len(name) > maxlen:
            # The adler32 CRC is returned as an int and can thus "seem" negative
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
        template_dirs = self._TemplateThemeDirs(**keywords)
        template = Template(self._log, file=template_file)
        result = template.Generate(keywords, template_dirs=template_dirs)
        return result

    def _DateAndTitleFromTitle(self, title, keywords=None):
        """
        Parses the a title and extract a date and the real title.
        Returns:
        - a tuple (datetime, title)
        - or (None, original title)
        """
        dt = None
        ti = title

        date_ymd_pattern = None
        if keywords:
            date_ymd_pattern = keywords.get("date_ymd_pattern")
        if not date_ymd_pattern:
            date_ymd_pattern = self._DATE_YMD

        m = date_ymd_pattern.match(title)

        if m:
            ti = (m.group("rest") or "")
            try:
                dt = datetime(int(m.group("year" ) or 0),
                              int(m.group("month") or 1),
                              int(m.group("day"  ) or 1),
                              int(m.group("hour" ) or 0),
                              int(m.group("min"  ) or 0),
                              int(m.group("sec"  ) or 0))
            except ValueError, e:
                self._log.Warn("Failed to extract date from title '%s': %s", title, str(e))

            # Fall back, trying again without the time part
            try:
                if dt is None:
                    dt = datetime(int(m.group("year" ) or 0),
                                  int(m.group("month") or 1),
                                  int(m.group("day"  ) or 1),
                                  0,
                                  0,
                                  0)
            except ValueError, e:
                # This time we don't ignore it. If you get an exception here, please
                # check your title or adjust the regexps for your site.
                self._log.Exception("Failed to extract date from title '%s': %s", title, str(e))
                raise

        # get the title, replacing all underscores by spaces
        # also collapse all whitespace to single space
        ti = re.sub("[ _\t\f\r\n]+", " ", ti)
        return (dt, ti.strip())

    def _GetMonth(self, _date):
        """
        Given a datetime object, returns a date with only the year and the
        month and the day set to 1.
        """
        return date(_date.year, _date.month, 1)

    def _ClearCache(self, site_settings):
        """
        Computes a "cache coherency" key that combines the current site
        settings, the rig version and the templates timestamps. Store
        this key in the cache. If we fail to find it, it means either that
        the cache was empty or that one of the parameters changed and we
        consequently clear the cache.
        """
        rig_version = Version()
        cache_coherency_key = {
            "site settings": site_settings,
            "theme": site_settings.theme,
            "theme dirs": self._TemplateThemeDirs(theme=site_settings.theme),
            "theme TS": PathTimestamp(self._TemplateThemeDirs(theme=site_settings.theme)),
            "rig3 vers str": rig_version.VersionString(),
            "rig3 svn rev": rig_version.SvnRevision()
            }
        hash_key = self._cache.GetKey(cache_coherency_key)

        f = self._hash_store.Contains(hash_key)

        if self._debug_cache:
            self._log.Debug("Cache Coherency key [site=%s, found=%s, hash=%s] = %s",
                            site_settings.public_name,
                            f,
                            hash_key,
                            repr(cache_coherency_key))

        if not f:
            self._log.Info("[%s] Clear Cache",
                           self._site_settings.public_name)
            self._cache.Clear()
            self._hash_store.Clear()
            self._hash_store.Add(hash_key)



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
