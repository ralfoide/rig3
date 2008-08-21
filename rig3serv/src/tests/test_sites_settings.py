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
from rig.sites_settings import SitesSettings, SiteSettings, IncludeExclude

#------------------------
class IncludeExcludeTest(RigTestCase):
    def testProcessIncludeExclude(self):
        s = IncludeExclude()
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "inc" })
        self.assertDictEquals({ "inc": True }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "*" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "$" })
        self.assertDictEquals({ SiteSettings.CAT_NOTAG: True }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "!exc" })
        self.assertEquals(None, s.cat_include)
        self.assertDictEquals({ "exc": True }, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "!*" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(SiteSettings.CAT_ALL, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "!$" })
        self.assertEquals(None, s.cat_include)
        self.assertDictEquals({ SiteSettings.CAT_NOTAG: True }, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "abc !def $ foo !$ !bfg !foo" })
        self.assertDictEquals({ "abc": True, SiteSettings.CAT_NOTAG: True, "foo": True }, s.cat_include)
        self.assertDictEquals({ "def": True, SiteSettings.CAT_NOTAG: True, "bfg": True, "foo": True }, s.cat_exclude)

        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "abc * def $ !foo !* !$ !bfg" })
        self.assertEquals(None, s.cat_include)
        self.assertEquals(SiteSettings.CAT_ALL, s.cat_exclude)
        
        # category names are case-insenstive, they are internally all lower-case
        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "foo Foo FooBar Bar bAr bar" })
        self.assertDictEquals({ "foo": True, "bar": True, "foobar": True }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

        # categories can be comma-separated or whitespace separated
        s = IncludeExclude()
        self.m._ProcessCatFilter(s, { "cat_filter": "   a,b c d\te,f,,g  h\t\ti , \t j " })
        self.assertDictEquals({ "a": True, "b": True, "c": True, "d": True,
                                "e": True, "f": True, "g": True, "h": True,
                                "i": True, "j": True, }, s.cat_include)
        self.assertEquals(None, s.cat_exclude)

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

    def testOverrideSourcesSettings(self):
        log = self.Log()

        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "file:/my/path1, rig_base:http://some/url" })
        self.assertListEquals(
            [ SourceFileReader(log, s, "/my/path1") ],
            s.source_list)
        self.assertDictEquals( { "rig_base": "http://some/url" },
            s.source_list[0]._source_settings.OverrideDict())

        s = SiteSettings()
        self.m._ProcessSources(s, { "sources": "dir:/my/path1,file:/my/path2, rig_base:http://some/url, file:/my/path3" })
        self.assertListEquals(
            [ SourceDirReader (log, s, "/my/path1"),
              SourceFileReader(log, s, "/my/path2"),
              SourceFileReader(log, s, "/my/path3") ],
            s.source_list)
        self.assertDictEquals( { "rig_base": "http://some/url" },
            s.source_list[0]._source_settings.OverrideDict())
        self.assertDictEquals( { "rig_base": "http://some/url" },
            s.source_list[1]._source_settings.OverrideDict())
        self.assertDictEquals( { "rig_base": "http://some/url" },
            s.source_list[2]._source_settings.OverrideDict())

    def testReformatLists(self):
        sites_set = SitesSettings(self.Log())
        
        s = SiteSettings()
        sites_set._ReformatLists(s)
        self.assertListEquals([], s.toc_categories)
        self.assertListEquals([], s.reverse_categories)

        s = SiteSettings()
        s.toc_categories = "mountain top hip hop"
        s.reverse_categories = "bikes hikes trikes"
        sites_set._ReformatLists(s)
        self.assertListEquals(["mountain", "top", "hip", "hop"], s.toc_categories)
        self.assertListEquals(["bikes", "hikes", "trikes"], s.reverse_categories)

    def testSiteSettingsTypes(self):
        """
        Validates that parameters in SiteSettings are of the correct type.
        """
        # all integer values
        s = SiteSettings(
                 rig_img_size=42,
                 header_img_height=43,
                 num_item_page=44,
                 num_item_atom=45
                 )
        self.assertEquals(42, s.rig_img_size)
        self.assertEquals(43, s.header_img_height)
        self.assertEquals(44, s.num_item_page)
        self.assertEquals(45, s.num_item_atom)

        # integer values will fail it set to none or not an integer
        self.assertRaises(TypeError,  SiteSettings, rig_img_size=None)
        self.assertRaises(ValueError, SiteSettings, rig_img_size="blah")

        self.assertRaises(TypeError,  SiteSettings, header_img_height=None)
        self.assertRaises(ValueError, SiteSettings, header_img_height="blah")

        self.assertRaises(TypeError,  SiteSettings, num_item_page=None)
        self.assertRaises(ValueError, SiteSettings, num_item_page="blah")

        self.assertRaises(TypeError,  SiteSettings, num_item_atom=None)
        self.assertRaises(ValueError, SiteSettings, num_item_atom="blah")


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
