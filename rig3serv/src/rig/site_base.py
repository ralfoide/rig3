#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site definition and actions

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



Workflow:
- rig3 uses rig.site.CreateSite(SiteSettings)
    - rig.site.CreateSite creates SiteDefault(SiteSettings)
        - creates SiteBase(SiteSettings)
- rig3 calls SiteBase.Process()                      (never overriden)
    - Call self.MakeDestDirs()                       (always overriden)
    - Call self._CopyMedia()                         (not overriden)
    - For each source: Call self._ProcessSourceItems (never overriden)
        - For each item: Calls self.GenerateItem     (always overriden)
    - Calls self._CollectCategories                  (never overriden)
    - Calls self.GeneratePages                       (always overriden)

Derives classes MUST implement:
- SiteBase.MakeDestDirs()
- SiteBase.GenerateItem()
- SiteBase.GeneratePages()


"""
__author__ = "ralfoide at gmail com"

import re
import os
import errno

from rig.template.template import Template
from rig.hashable import Hashable
from rig import stats

DEFAULT_THEME = "default"


#------------------------
class SiteItem(Hashable):
    """
    Represents an item:
    - list of categories (list of string)
    - content_gen: A method (lambda) that generates the data of the entry
    - date (datetime)
    - title (string)
    - permalink: (string) The permalink URL relative from the base site.
    - source_item (SourceItem)
    """
    def __init__(self, source_item, date, title, permalink, content_gen, categories=None):
        super(SiteItem, self).__init__()
        self.source_item = source_item
        self.date = date
        self.title = title
        self.content_gen = content_gen
        self.categories = categories or []
        self.permalink = permalink

    def __eq__(self, rhs):
        """
        Two site items are equal if they have the same date,
        categories and relative filename.

        Note: avoid comparing content_gen since it's a lambda and in the
        current implementation is basically a function pointer with no
        obvious relation to the method implementation.
        """
        if isinstance(rhs, SiteItem):
            return (self.date == rhs.date and
                    self.categories == rhs.categories)
        return False

    def RigHash(self, md=None):
        # Note: do not hash content_gen as it's an internal pointer that
        # changes between runs.
        md = self.UpdateHash(md, self.source_item)
        md = self.UpdateHash(md, self.date)
        md = self.UpdateHash(md, self.title)
        md = self.UpdateHash(md, self.categories)
        md = self.UpdateHash(md, self.permalink)
        return md

    def __repr__(self):
        try:
            # Note: do not display content_gen as it's an internal pointer that
            # changes between runs.
            return "[%s: %s, %s, %s, %s, %s]" % (
                     self.__class__.__name__,
                     self.source_item,
                     self.date,
                     self.title,
                     self.categories,
                     self.permalink)
        except:
            return super(SiteItem, self).__repr__()


#------------------------
class SiteBase(object):
    """
    Base class to generate sites.

    This class is "abstract". Some methds must be derived to define a proper behavior.
    """
    MEDIA_DIR = "media"
    DIR_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2})?)[ _-] *(?P<name>.*) *$")
    VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")

    def __init__(self, log, dry_run, force, site_settings):
        self._log = log
        self._dry_run = dry_run
        self._force = force
        self._site_settings = site_settings

    # Derived class must implement this to define the desired behavior

    def Dispose(self):
        """
        Callers should call this when they will no longer need to use a site.

        Subclassing: Derived classes should override this to release any
        temporary resources.
        """
        pass

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

    def GenerateItem(self, source_item):
        """
        Generates a new photoblog entry, which may have an index and/or may
        have an album.

        Returns a SiteItem that describes an entry for the site's pages.

        If the source item is not suitable (i.e. generates no data),
        the method must return None and the caller must be prepared to ignore it.

        This basically converts a SourceItem into a SiteItem.

        Arguments:
        - source_item: An instance of SourceItem.

        Subclassing: Derived classes MUST override this and not call the parent.
        """
        raise NotImplementedError("Must be derived by subclasses")

    # Generic implementation that is not expected to be derived.

    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """
        self._log.Info("[%s] Processing site:\n  Source: %s\n  Dest: %s\n  Theme: %s",
                       self._site_settings.public_name,
                       self._site_settings.source_list,
                       self._site_settings.dest_dir,
                       self._site_settings.theme)
        self.MakeDestDirs()
        self._CopyMedia()
        site_items = []

        s = stats.Start("1-parse")

        dups = {}

        for source in self._site_settings.source_list:
            self._ProcessSourceItems(source, site_items, dups)

        del dups

        s.Stop(len(site_items))

        categories = self._CollectCategories(site_items)

        self._log.Info("[%s] Found %d site_items, %d categories",
               self._site_settings.public_name,
               len(site_items), len(categories))

        s = stats.Start("2-gen")

        self.GeneratePages(categories, site_items)

        s.Stop(len(site_items))

    def _CopyMedia(self):
        """
        Copy media directory from selected template to destination

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.
        """
        _keywords = { "base_url": self._site_settings.base_url,
                      "public_name": self._site_settings.public_name }
        def _apply_template(source, dest):
            # Use fill template to copy/transform the file
            template = Template(self._log, file=source)
            result = template.Generate(_keywords)
            fdest = file(dest, "wb")
            fdest.write(result)
            fdest.close()

        media = self._TemplatePath(self.MEDIA_DIR)
        if os.path.isdir(media):
            self._CopyDir(media, os.path.join(self._site_settings.dest_dir, self.MEDIA_DIR),
                          filter_ext={ ".css": _apply_template })

    def _ProcessSourceItems(self, source, in_out_items, dups):
        """
        Process all items from a given source and queue them into the
        in_out_items list.

        This basically converts a list of SourceItem into a list of SiteItem.

        'dups' is a int-out hash set where all items processed are kept
        indexed by their rig hash. The hash set is shared accross all the
        sources of the same site, thus allowing to avoid duplicate entries in
        the site. However this only works for symlinked entries since the
        real path of the entry is computed in the hash.

        Subclassing: Derived classes can override this if needed.
        The base implementation is expected to be good enough.

        Returns in_out_items, which is a list of SiteItems.
        """
        dup_on_realpath = self._site_settings.dup_on_realpath

        for source_item in source.Parse(self._site_settings.dest_dir):
            if dup_on_realpath:
                item_hash = source_item.ContentHash().hexdigest()
            else:
                item_hash = source_item.RigHash().hexdigest()
            self._log.Debug("New Source Item [#%s]: %s", item_hash, repr(source_item))
            if item_hash in dups:
                self._log.Info("Skipping dup source item %s", source_item.PrettyRepr())
            else:
                dups[item_hash] = source_item
                site_item = self.GenerateItem(source_item)
                if site_item:
                    in_out_items.append(site_item)
        return in_out_items

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the theme's template directory.

        The default is to extract the theme given as a keyword parameter,
        or to get the theme from the site site_settings.

        Returns an os.path.join of _TemplateDir, theme and path.

        Subclassing: some site generators may want to override the theme
        name used for the template directory (for example to always return
        stuff from the default directory.) Mock objects might want to change
        the _TemplateDir method instead.
        """
        if keywords and "theme" in keywords:
            theme = keywords["theme"]
        else:
            theme = self._site_settings.theme
        return os.path.join(self._TemplateDir(), theme, path)

    def _TemplateThemeDirs(self, **keywords):
        """
        Returns the list(str) of all possible directories matching the
        current theme.
        The theme name is looked for the keyword or in the current site_settings.

        In the base version, this is the same as the path used by
        _TemplatePath. However derived implementations can add their own
        custom template path to the list.

        Subclassing: This must never returns None nor an empty list.
        """
        if keywords and "theme" in keywords:
            theme = keywords["theme"]
        else:
            theme = self._site_settings.theme
        return [ os.path.join(self._TemplateDir(), theme) ]

    # Utilities, overridable for unit tests

    def _CollectCategories(self, site_items):
        """
        Get all categories used in all site items.
        Returns a list of string, sorted.

        Subclassing: There should be no need to override this.
        """
        categories = {}
        for item in site_items:
            if item:
                for c in item.categories:
                    categories[c] = 1
        categories = categories.keys()
        categories.sort()
        return categories

    def _TemplateDir(self):
        """
        Returns the template dir from the site site_settings.
        If it doesn't exist, returns the path to the the implicit "templates"
        directory relative to this source file.
        """
        if self._site_settings.template_dir:
            return self._site_settings.template_dir
        else:
            f = __file__
            return os.path.realpath(os.path.join(os.path.dirname(f), "..", "..", "templates"))

    def _MkDestDir(self, rel_dir):
        """
        Creates a directory in the site's dest_dir.
        Doesn't generate an error if the directory already exists.
        """
        try:
            os.makedirs(os.path.join(self._site_settings.dest_dir, rel_dir))
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def _CopyDir(self, source_dir, dest_dir,
                 skip=[ "CVS", ".svn" ],
                 filter_ext={}):
        """
        Copies a directory (recursively, with all its content) into
        a given destination. Overwrites existing content. This doesn't
        clean the output so it will merge with existing content, if any.
        Also it will fail if:
        - the destination is not a directory
        - the destination is not writable/executable

        filter_ext is a dict { extension => filter_method }.
        Methods should have a signature (source_name, dest_name) and should
        copy the source to the dest, using whatever transformation desired.
        Extensions must start with dot in them (i.e. ".css", not "css")
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
