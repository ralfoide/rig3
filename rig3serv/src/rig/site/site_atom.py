#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "atom" theme 

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import time
from datetime import datetime

from rig.version import Version
from rig.site.site_default import SiteDefault

#------------------------
class SiteAtom(SiteDefault):
    """
    Describes how to generate the content of a site using the "atom" theme.
    
    The "atom" theme inherits from the "default" theme and and changes the
    behavior to create an Atom feed.
    """

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the default theme's template
        directory.
        """
        return super(SiteAtom, self)._TemplatePath(path, theme="atom")

    def MakeDestDirs(self):
        """
        No directories to create here.
        Returns self for chaining
        """
        return self

    def GeneratePages(self, categories, items):
        """
        Generates one "page", which is the atom feed of all entries.

        Input:
        - categories: list of categories accumulated from each entry
        - items: list of SiteItem
        """
        # Sort by decreasing date (i.e. compares y to x, not x to y)
        items.sort(lambda x, y: cmp(y.date, x.date))

        # we skip categories if there's only one of them
        if len(categories) == 1:
            categories = []

        # Generate an index page with all posts (whether they have a category or not)
        self._GenerateAtomFeed(categories, items)
    
    def _GenerateAtomFeed(self, all_categories, items):

        filename = "atom.xml"

        keywords = self._settings.AsDict()
        keywords["title"] = "All Items"
        keywords["last_gen_ts"] = datetime.today()
        keywords["all_categories"] = all_categories
        version = Version()
        keywords["rig3_version"] = "%s-%s" % (version.VersionString(),
                                              version.SvnRevision())


        entries = []
        older_date = None
        for i in items:
            # SiteItem.content_gen is a lambda that generates the content
            entries.append(i.content_gen("entry.xml", keywords))
            older_date = (older_date is None) and i.date or max(older_date, i.date)

        keywords["entries"] = entries
        keywords["last_content_ts"] = older_date

        # Converts last_content_ts to UTC and prints its ISO8601
        keywords["last_content_iso"] = datetime.utcfromtimestamp(
                             time.mktime(time.gmtime(time.mktime(
                                 keywords["last_gen_ts"].timetuple() )))).isoformat() + "Z"
        
        content = self._FillTemplate("feed.xml", **keywords)
        self._WriteFile(content, self._settings.dest_dir, filename)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
