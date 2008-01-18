#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Settings

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase

import rig3
from rig.source_reader import SourceDirReader, SourceFileReader
from rig.sites_settings import SitesSettings, SiteSettings

#------------------------
class SitesSettingsTest(RigTestCase):

    def setUp(self):
        self.m = SitesSettings(self.Log())

    def tearDown(self):
        self.m = None

    def testTestdata(self):
        p = self.getTestDataPath()
        r = self.m.Load(os.path.join(p, "sites_settings.rc"))
        self.assertSame(r, self.m)
        self.assertListEquals(["site1", "site2"], self.m.Sites())

        s = self.m.GetSiteSettings("site1")
        self.assertNotEquals(None, s)
        self.assertIsInstance(SiteSettings, s)
        self.assertEquals("blue_template", s.theme)
        self.assertEquals("Site 1", s.public_name)
        self.assertListEquals(
            [ SourceDirReader(self.Log(), s, "/tmp/data/site1") ],
            s.source_list)
        self.assertEquals("/tmp/generated/site1", s.dest_dir)

    def testProcessSources(self):
        log = self.Log()
        s = SiteSettings()
        self.assertListEquals([], s.source_list)

        # Invalid sources (no qualifier)
        self.m._ProcessSources(s, { "var1": "path1", "var2": "path2" })
        self.assertListEquals([], s.source_list)

        # SourceDirReader
        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "dir:/my/path1" })
        self.assertListEquals(
            [ SourceDirReader(log, s, "/my/path1") ],
            s.source_list)

        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": '  dir :  "/my/path1,path2"  ' })
        self.assertListEquals(
            [ SourceDirReader(log, s, "/my/path1,path2") ],
            s.source_list)
        
        # SourceFileReader
        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "file:/my/path1" })
        self.assertListEquals(
            [ SourceFileReader(log, s, "/my/path1") ],
            s.source_list)

        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": '  file :  "/my/path1,path2"  ' })
        self.assertListEquals(
            [ SourceFileReader(log, s, "/my/path1,path2") ],
            s.source_list)

        # Combined
        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "dir:/my/path1,file:/my/path2" })
        self.assertListEquals(
            [ SourceDirReader (log, s, "/my/path1"),
              SourceFileReader(log, s, "/my/path2") ],
            s.source_list)

        # All
        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "all:/my/path1" })
        self.assertListEquals(
            [ SourceDirReader (log, s, "/my/path1"),
              SourceFileReader(log, s, "/my/path1") ],
            s.source_list,
            sort=True)

    def testProcessCatFilter(self):
        s = SiteSettings()
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "inc" })
        self.assertDictEquals({ "inc": True }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "*" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "$" })
        self.assertDictEquals({ SiteSettings.CAT_NOTAG: True }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "!exc" })
        self.assertEquals(None, s.cat_include)
        self.assertDictEquals({ "exc": True }, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "!*" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(SiteSettings.CAT_ALL, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "!$" })
        self.assertEquals(None, s.cat_include)
        self.assertDictEquals({ SiteSettings.CAT_NOTAG: True }, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "abc !def $ foo !$ !bfg !foo" })
        self.assertEquals({ "abc": True, SiteSettings.CAT_NOTAG: True, "foo": True }, s.cat_include)
        self.assertEquals({ "def": True, SiteSettings.CAT_NOTAG: True, "bfg": True, "foo": True }, s.cat_exclude)

        s = SiteSettings()
        self.m._ProcessCatFilter(s, { "cat_filter": "abc * def $ !foo !* !$ !bfg" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(SiteSettings.CAT_ALL, s.cat_exclude)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
