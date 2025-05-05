#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

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

import os
import types
from datetime import datetime

from tests.rig_test_case import RigTestCase

from rig.site.site_default import SiteDefault, ContentEntry
from rig.site_base import DEFAULT_THEME, SiteItem
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir, RelFile
from rig.source_reader import SourceDirReader
from rig.source_item import SourceDir, SourceSettings, SourceContent
from rig.sites_settings import SiteSettings, SitesSettings
from rig.sites_settings import DEFAULT_ITEMS_PER_PAGE

#------------------------
class MockSiteDefault(SiteDefault):
    """
    Behaves like a SiteDefault() but overrides the base template directory location
    to use testdata/templates instead.

    Also traps the last _Filltemplate parameters.
    """
    def __init__(self, test_case, log, dry_run, force, site_settings):
        self._test_case = test_case
        self._fill_template_params = {}
        self._write_file_params = []
        super(MockSiteDefault, self).__init__(log, dry_run, force, site_settings)

        # override the Cache.Clear method by ours
        self._cache_clear_count = 0
        self._org_cache_clear = self._cache.Clear
        setattr(self._cache, "Clear", self._CacheClearOverride)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

    def _FillTemplate(self, template, **keywords):
        """
        Keeps a copy of the _FillTemplate parameters and then calls the original.
        Trapped parameters are available in
          self._fill_template_params[template] => list(keyword dict.)
        """
        if not template in self._fill_template_params:
            self._fill_template_params[template] = []
        self._fill_template_params[template].append(dict(keywords))
        return super(MockSiteDefault, self)._FillTemplate(template, **keywords)

    def _WriteFile(self, data, dest_dir, leafname):
        """
        Keeps a copy of all parameters given to _WriteFile.
        This implementation does NOT call the base class so that nothing gets
        written anywhere.

        Trapped parameters are available in
          self._write_file_params => list(data, dest_dir, leafname)
        See GetWriteFileData(n, m) below.
        """
        self._write_file_params.append((data, dest_dir, leafname))

    _DATA = 0
    _DEST_DIR = 1
    _LEAFNAME = 2

    def GetWriteFileData(self, tuple_index):
        """
        Returns a *copy* of the self._write_file_params list
        with items rearranged.
        - tuple_index: _DATA, _DEST_DIR or _LEAFNAME, the value to return.

        This basically remaps (data, dest_dir, leafname) to whatever you like
        to test, e.g. list[ value: leafname ] or list[ value: data ].
        """
        return [ p[tuple_index] for p in self._write_file_params ]

    def _CacheClearOverride(self):
        """
        Override self._cache.Clear to count the number of calls then
        call the original implementation.
        """
        self._cache_clear_count += 1
        self._org_cache_clear()

    def CacheClearCount(self, reset):
        """
        Returns the number of cache clear done so far.
        If reset is true, resets the count to 0.
        """
        c = self._cache_clear_count
        if reset:
            self._cache_clear_count = 0
        return c

#------------------------
class SiteDefaultTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        self.sis, self.sos = self._computeSisSos()

        self.keywords = self.sis.AsDict()
        self.keywords.update(self.sos.AsDict())

    def _computeSisSos(self):
        source = SourceDirReader(self.Log(),
                                 site_settings=None,
                                 source_settings=None,
                                 path=os.path.join(self.getTestDataPath(), "album"))
        sis = SiteSettings(public_name="Test Album",
                           source_list=[ source ],
                           dest_dir=self._tempdir,
                           cache_dir=self._cachedir,
                           theme=DEFAULT_THEME,
                           base_url="http://www.example.com",
                           encoding="iso-8859-1")
        sos = SourceSettings(rig_base="http://example.com/photos/index.php")
        return sis, sos

    def tearDown(self):
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testSimpleFileName(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc///de\\\\f/g\\h"))
        self.assertEquals("a-ab_12_txt", m._SimpleFileName("a//\\ab!@#$12%^&@&*()_+.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt", maxlen=20))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))

        # the default for mangled_name_len is 50
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof",
                                                                          self.sis.mangled_name_len))
        self.sis.mangled_name_len = 25
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof"))
        # 0 deactivates the mangling
        self.sis.mangled_name_len = 0
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof"))

    def testFillTemplate(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        keywords = dict(self.keywords)
        keywords["title"] = "MyTitle"
        keywords["entries"] = [
           ContentEntry("content entry1", "entry1", None, "url1"),
           ContentEntry("content entry2", "entry2", None, "url2") ]
        keywords["curr_category"] = ""
        keywords["all_categories"] = []
        keywords["toc_categories"] = []
        keywords["last_gen_ts"] = datetime(2007, 11, 12, 14, 15, 16)
        keywords["last_content_ts"] = datetime(2001, 3, 14, 15, 9, 2)
        keywords["rig3_version"] = "3.1.4.15"

        html = m._FillTemplate(SiteDefault._TEMPLATE_HTML_INDEX, **keywords)
        self.rigAssertIsInstance(str, html)
        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertDictEquals(keywords, m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))
        self.assertHtmlEquals(
            r"""<html lang="en-US">
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                <link rel="stylesheet" type="text/css" href="media/style.css" />
                <title>Test Album - MyTitle</title>
                </head>
                <body>
                (placeholder for image header)<br/>
                blog name is Test Album<br/>
                categories are All<br/>
                content entry1
                content entry2
                <p>
                Most recent entry: 2001-03-14 15:09:02 --
                Generated on 2007-11-12 14:15:16 by <a href="http://code.google.com/p/rig3/">Rig3 3.1.4.15</a>
                </body>
                </html>""",
            html)

        keywords = dict(self.keywords)
        keywords["title"] = "MyTitle"
        keywords["sections"] = { "en": "Main <b>Text Content</b> as HTML",
                                 "images": "<a href='page_url'><img src='image_url'/></a>" }
        html = m._FillTemplate(SiteDefault._TEMPLATE_HTML_ENTRY, **keywords)
        self.rigAssertIsInstance(str, html)
        self.assertTrue(SiteDefault._TEMPLATE_HTML_ENTRY in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_ENTRY]))
        self.assertDictEquals(keywords, m._fill_template_params[SiteDefault._TEMPLATE_HTML_ENTRY][0])
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))
        self.assertHtmlEquals(
            r"""<div class="entry">
                <h2>MyTitle</h2>
                Main <b>Text Content</b> as HTML
                <br/>
                <a href='page_url'><img src='image_url'/></a>
                <br/>
                </div>
                """,
            html)

    def testDateAndTitleFromTitle(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        self.assertEquals((None, "27"),        m._DateAndTitleFromTitle("27"))
        self.assertEquals((None, "2007"),      m._DateAndTitleFromTitle("2007"))
        self.assertEquals((None, "2007-1"),    m._DateAndTitleFromTitle("2007-1"))

        # lack of day is the same as using day=01
        self.assertEquals((datetime(2007, 10, 1), ""),
                          m._DateAndTitleFromTitle("2007-10"))

        # here we don't interpret "YYYYMM[-]2" as a day because it lacks 2 digits,
        # instead it gets interpreted as the title.
        self.assertEquals((datetime(2007, 10, 1), "2"),
                          m._DateAndTitleFromTitle("2007102"))
        self.assertEquals((datetime(2007, 10, 1), "2"),
                          m._DateAndTitleFromTitle("2007-10-2"))

        self.assertEquals((datetime(2007, 10, 27), ""),
                          m._DateAndTitleFromTitle("20071027"))
        self.assertEquals((datetime(2007, 10, 27), "rest"),
                          m._DateAndTitleFromTitle("2007-10-27 rest"))
        self.assertEquals((datetime(2007, 10, 27), "rest of the line.."),
                          m._DateAndTitleFromTitle("2007/10/27_rest of the line.."))
        self.assertEquals((datetime(2007, 10, 27), "whitespace"),
                          m._DateAndTitleFromTitle("2007-10/27    whitespace   "))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("20071027121314"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10-27-12-13-14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10-27 12-13-14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007/10/27 12:13:14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10/27,12/13/14"))

        self.assertEquals((None, "white space"),  m._DateAndTitleFromTitle("_white space_"))
        self.assertEquals((None, "white space"),  m._DateAndTitleFromTitle("_white_space_"))
        self.assertEquals((None, "white space"),  m._DateAndTitleFromTitle("  ___\twhite_\r\n\f_  __space_   \r\t\n\f___ "))


    def testDateAndTitleFromTitle_ErrorCases(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        # Hour is invalid: 44>23... log warning and ignore hour in this case
        self.assertEquals((datetime(2007, 10, 27), ""),
                          m._DateAndTitleFromTitle("20071027-4400"))

        # Day must be in 1..31
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "20071034")

        # Month must be in 1..12
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "20071527")

        # Year must be in range 1..9999
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "00001027")
        self.assertEquals((datetime(1, 10, 27), ""),
                          m._DateAndTitleFromTitle("00011027"))
        self.assertEquals((datetime(9999, 10, 27), ""),
                          m._DateAndTitleFromTitle("99991027"))

    def testGenerateItems_Izu(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album", "blog1")
        item = m.GenerateItem(SourceDir(datetime.today(),
                                        RelDir(source_dir, "2007-10-07_Folder 1"),
                                        [ "index.izu" ],
                                        self.sos))
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2007, 10, 07), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+</div>', item.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY))
        self.assertListEquals([ "foo", "bar", "other" ], item.categories, sort=True)

    def testGenerateItems_Html(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album", "blog2")
        item = m.GenerateItem(SourceDir(datetime.today(),
                                        RelDir(source_dir, "2006-05_Movies"),
                                        [ "index.html" ],
                                        self.sos))
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2006, 5, 28, 17, 18, 5), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+<!-- \[izu:.+\] -->blog 2 <table.+>.+</table>.+</div>',
                               item.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY))
        self.assertListEquals([ "videos" ], item.categories, sort=True)

    def testImgPattern(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()
        self.assertEquals(None, m._IMG_PATTERN.match("myimage.jpg"))
        self.assertEquals(None, m._IMG_PATTERN.match("PICT1200.jpg"))
        self.assertEquals(None, m._IMG_PATTERN.match("R12345-Some Name.bmp"))
        self.assertEquals(None, m._IMG_PATTERN.match("R12345-Some Name.gif"))
        self.assertDictEquals({ "index": "1000",
                                "rating": "_",
                                "name": " Old Index ",
                                "ext": ".jpg" },
                              m._IMG_PATTERN.match("1000_ Old Index .jpg").groupdict())
        self.assertDictEquals({ "index": "R12345",
                                "rating": "_",
                                "name": "Some Name",
                                "ext": ".jpg" },
                              m._IMG_PATTERN.match("R12345_Some Name.jpg").groupdict())
        self.assertDictEquals({ "index": "X12345",
                                "rating": "-",
                                "name": "Some Movie",
                                "ext": ".original.mov" },
                              m._IMG_PATTERN.match("X12345-Some Movie.original.mov").groupdict())
        self.assertDictEquals({ "index": "Y31415",
                                "rating": "+",
                                "name": "Web Version",
                                "ext": ".web.mov" },
                              m._IMG_PATTERN.match("Y31415+Web Version.web.mov").groupdict())
        self.assertDictEquals({ "index": "Z31415",
                                "rating": ".",
                                "name": "Web Version",
                                "ext": ".web.wmv" },
                              m._IMG_PATTERN.match("Z31415.Web Version.web.wmv").groupdict())

    def testGetRigLink(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        expected = (
            '<a title="2007-11-08 Album Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg">'
            '<img title="Best of 2007" alt="Best of 2007" src="http://example.com/photos/index.php?th=&album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg&sz=400&q=75"/>'
            '</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(self.keywords,
                          RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
                          "Best of 2007.jpg",
                          400))

        expected = (
            '<a title="2007-11-08 Album Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg">'
            '<img title="Best of 2007" alt="Best of 2007" src="http://example.com/photos/index.php?th=&album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg&sz=-1&q=75"/>'
            '</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(self.keywords,
                          RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
                          "Best of 2007.jpg",
                          -1))

        expected = (
            '<a title="2007-11-08 Album &amp; Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20%26%20Title">'
            '2007-11-08 Album &amp; Title</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(self.keywords,
                          RelDir("base", "My Albums/Year_2007/2007-11-08 Album & Title"),
                          None,
                          -1))

    def testGenerateImages(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        keywords = self.keywords

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [], keywords))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "index.izu",
                                                    "index.html",
                                                    "image.jpeg" ],
                                                  keywords ))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "J1234_sound.mp3" ], keywords))

        self.assertHtmlEquals(
            "See more images for " + m._GetRigLink(keywords, RelDir("base", ""), None, -1),
            m._GenerateImages(RelDir("base", ""), [ "J1234.image.jpg" ], keywords))

        self.assertHtmlEquals(
            '<table class="image-table"><tr><td>\n' + m._GetRigLink(keywords, RelDir("base", ""), "J1234-image.jpg", 300) + '</td></tr></table>',
            m._GenerateImages(RelDir("base", ""), [ "J1234-image.jpg" ], keywords))

    def testGenerateIndexPage(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        m._GenerateIndexPage(
             path="",
             rel_base="",
             curr_category=None,
             all_categories=[],
             items=[],
             month_pages=[])
        params = m._fill_template_params

        for key in [ "rig_img_url",
                     "rig_thumb_url",
                     "source_list",
                     "header_img_height",
                     "tracking_code",
                     "header_img_url",
                     "rig_album_url",
                     "img_gen_script",
                     "entries",
                     "last_content_ts",
                     "rig_img_size",
                     "month_pages",
                     "rig3_version",
                     "title",
                     "rel_base_url",
                     "base_url",
                     "public_name",
                     "theme",
                     "all_categories",
                     "dest_dir",
                     "cat_filter",
                     "toc_categories",
                     "last_gen_ts" ]:
            self.assertTrue(key in params[SiteDefault._TEMPLATE_HTML_INDEX][0],
                            "Missing [%s] in %s" % (key, params))

    def testRigAlbumLink(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        keywords = self.keywords
        keywords.update(SourceSettings(rig_base=None).AsDict())
        self.assertEquals("", m._RigAlbumLink(keywords, "my album"))

        keywords.update(SourceSettings(rig_base="http://my.rig/index.php").AsDict())
        self.assertEquals("http://my.rig/index.php?album=my%20album",
                          m._RigAlbumLink(keywords, "my album"))

    def testRigImgLink(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        keywords = self.keywords
        keywords.update(SourceSettings(rig_base=None).AsDict())
        self.assertEquals("", m._RigImgLink(keywords, "my album", "my image.jpg"))

        keywords.update(SourceSettings(rig_base="http://my.rig/index.php").AsDict())
        self.assertEquals("http://my.rig/index.php?album=my%20album&img=my%20image.jpg",
                          m._RigImgLink(keywords, "my album", "my image.jpg"))

    def testRigThumbLink(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        keywords = self.keywords
        keywords.update(SourceSettings(rig_base=None).AsDict())
        self.assertEquals("", m._RigThumbLink(keywords, "my album", "my image.jpg", 640))

        keywords.update(SourceSettings(rig_base="http://my.rig/index.php").AsDict())
        self.assertEquals("http://my.rig/index.php?th=&album=my%20album&img=my%20image.jpg&sz=640&q=75",
                          m._RigThumbLink(keywords, "my album", "my image.jpg", 640))

    def testGeneratePages_0Empty(self):
        """
        Printing an empty list of items only generates an index page
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))

        m.GeneratePages(categories=[], items=[])
        self.assertListEquals([ "index.html", "atom.xml" ], m.GetWriteFileData(m._LEAFNAME))

    def testGeneratePages_0Cats(self):
        """
        Printing 3 times + 1 the number of items per page generates 4 pages
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = []
        for x in xrange(0, DEFAULT_ITEMS_PER_PAGE * 3 + 1):
            # x % 12 => we'll generate 12 month pages
            si = SiteItem(source_item=None,
                          date=datetime(2000, 1 + (x % 12), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)

        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-12.html", "2000-11.html", "2000-10.html", "2000-09.html",
            "2000-08.html", "2000-07.html", "2000-06.html", "2000-05.html",
            "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            "post_2000-12-24_blah.html",
            "post_2000-12-20_blah.html",
            "post_2000-12-12_blah.html",
            "post_2000-12-08_blah.html",
            "post_2000-12-04_blah.html",
            "post_2000-11-23_blah.html",
            "post_2000-11-19_blah.html",
            "post_2000-11-11_blah.html",
            "post_2000-11-07_blah.html",
            "post_2000-11-03_blah.html",
            "post_2000-10-22_blah.html",
            "post_2000-10-18_blah.html",
            "post_2000-10-10_blah.html",
            "post_2000-10-06_blah.html",
            "post_2000-10-02_blah.html",
            "post_2000-09-21_blah.html",
            "post_2000-09-17_blah.html",
            "post_2000-09-09_blah.html",
            "post_2000-09-05_blah.html",
            "post_2000-09-01_blah.html",
            "post_2000-08-28_blah.html",
            "post_2000-08-20_blah.html",
            "post_2000-08-16_blah.html",
            "post_2000-08-08_blah.html",
            "post_2000-08-04_blah.html",
            "post_2000-07-27_blah.html",
            "post_2000-07-19_blah.html",
            "post_2000-07-15_blah.html",
            "post_2000-07-07_blah.html",
            "post_2000-07-03_blah.html",
            "post_2000-06-26_blah.html",
            "post_2000-06-18_blah.html",
            "post_2000-06-14_blah.html",
            "post_2000-06-06_blah.html",
            "post_2000-06-02_blah.html",
            "post_2000-05-25_blah.html",
            "post_2000-05-17_blah.html",
            "post_2000-05-13_blah.html",
            "post_2000-05-05_blah.html",
            "post_2000-05-01_blah.html",
            "post_2000-04-28_blah.html",
            "post_2000-04-24_blah.html",
            "post_2000-04-16_blah.html",
            "post_2000-04-12_blah.html",
            "post_2000-04-04_blah.html",
            "post_2000-03-27_blah.html",
            "post_2000-03-23_blah.html",
            "post_2000-03-15_blah.html",
            "post_2000-03-11_blah.html",
            "post_2000-03-03_blah.html",
            "post_2000-02-26_blah.html",
            "post_2000-02-22_blah.html",
            "post_2000-02-14_blah.html",
            "post_2000-02-10_blah.html",
            "post_2000-02-02_blah.html",
            "post_2000-01-25_blah.html",
            "post_2000-01-21_blah.html",
            "post_2000-01-13_blah.html",
            "post_2000-01-09_blah.html",
            "post_2000-01-05_blah.html",
            "post_2000-01-01_blah.html",
             ],
          m.GetWriteFileData(m._LEAFNAME))

        # check that "all_entries" in index & month pages contain the full list
        # of items, not just the ones for the page (i.e. all_entries != entries)
        self.assertTrue(SiteDefault._TEMPLATE_HTML_MONTH in m._fill_template_params)
        for keywords in m._fill_template_params[SiteDefault._TEMPLATE_HTML_MONTH]:
            self.assertEquals(len(items), len(keywords["all_entries"]))

        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        for keywords in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]:
            self.assertEquals(len(items), len(keywords["all_entries"]))

    def testGeneratePages_1Cat(self):
        """
        Print items with only one category, this does not generate
        category indexes.
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = [ "first" ]
        for x in xrange(0, DEFAULT_ITEMS_PER_PAGE + 1):
            # x % 7 => we'll generate 7 month pages
            si = SiteItem(source_item=None,
                          date=datetime(2000, 1 + (x % 7), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)

        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-07.html", "2000-06.html", "2000-05.html",
            "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
#            "post_2000-07-21_blah.html",TODO EDIT
#            "post_2000-07-14_blah.html",
#            "post_2000-07-07_blah.html",
#            "post_2000-06-20_blah.html",
#            "post_2000-06-13_blah.html",
#            "post_2000-06-06_blah.html",
#            "post_2000-05-19_blah.html",
#            "post_2000-05-12_blah.html",
#            "post_2000-05-05_blah.html",
#            "post_2000-04-18_blah.html",
#            "post_2000-04-11_blah.html",
#            "post_2000-04-04_blah.html",
#            "post_2000-03-17_blah.html",
#            "post_2000-03-10_blah.html",
#            "post_2000-03-03_blah.html",
#            "post_2000-02-16_blah.html",
#            "post_2000-02-09_blah.html",
#            "post_2000-02-02_blah.html",
#            "post_2000-01-15_blah.html",
#            "post_2000-01-08_blah.html",
            ],
          m.GetWriteFileData(m._LEAFNAME))

    def testGeneratePages_2Cats(self):
        """
        With two categories, we get category pages too
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = [ "first", "second" ]
        for x in xrange(0, DEFAULT_ITEMS_PER_PAGE + 1):
            # x % 5 => we'll generate 5 month pages
            si = SiteItem(source_item=None,
                          date=datetime(2000, 1 + (x % 5), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)

        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-05.html", "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            os.path.join("cat", "first", "2000-05.html"),
            os.path.join("cat", "first", "2000-04.html"),
            os.path.join("cat", "first", "2000-03.html"),
            os.path.join("cat", "first", "2000-02.html"),
            os.path.join("cat", "first", "2000-01.html"),
            os.path.join("cat", "first", "index.html"),
            os.path.join("cat", "first", "atom.xml"),
            os.path.join("cat", "first", "post_2000-05-20_blah.html"),
            os.path.join("cat", "first", "post_2000-05-15_blah.html"),
            os.path.join("cat", "first", "post_2000-05-10_blah.html"),
            os.path.join("cat", "first", "post_2000-05-05_blah.html"),
            os.path.join("cat", "first", "post_2000-04-19_blah.html"),
            os.path.join("cat", "first", "post_2000-04-14_blah.html"),
            os.path.join("cat", "first", "post_2000-04-09_blah.html"),
            os.path.join("cat", "first", "post_2000-04-04_blah.html"),
            os.path.join("cat", "first", "post_2000-03-18_blah.html"),
            os.path.join("cat", "first", "post_2000-03-13_blah.html"),
            os.path.join("cat", "first", "post_2000-03-08_blah.html"),
            os.path.join("cat", "first", "post_2000-03-03_blah.html"),
            os.path.join("cat", "first", "post_2000-02-17_blah.html"),
            os.path.join("cat", "first", "post_2000-02-12_blah.html"),
            os.path.join("cat", "first", "post_2000-02-07_blah.html"),
            os.path.join("cat", "first", "post_2000-02-02_blah.html"),
            os.path.join("cat", "first", "post_2000-01-21_blah.html"),
            os.path.join("cat", "first", "post_2000-01-16_blah.html"),
            os.path.join("cat", "first", "post_2000-01-11_blah.html"),
            os.path.join("cat", "first", "post_2000-01-06_blah.html"),
            os.path.join("cat", "first", "post_2000-01-01_blah.html"),
            os.path.join("cat", "second", "2000-05.html"),
            os.path.join("cat", "second", "2000-04.html"),
            os.path.join("cat", "second", "2000-03.html"),
            os.path.join("cat", "second", "2000-02.html"),
            os.path.join("cat", "second", "2000-01.html"),
            os.path.join("cat", "second", "index.html"),
            os.path.join("cat", "second", "atom.xml"),
            os.path.join("cat", "second", "post_2000-05-20_blah.html"),
            os.path.join("cat", "second", "post_2000-05-15_blah.html"),
            os.path.join("cat", "second", "post_2000-05-10_blah.html"),
            os.path.join("cat", "second", "post_2000-05-05_blah.html"),
            os.path.join("cat", "second", "post_2000-04-19_blah.html"),
            os.path.join("cat", "second", "post_2000-04-14_blah.html"),
            os.path.join("cat", "second", "post_2000-04-09_blah.html"),
            os.path.join("cat", "second", "post_2000-04-04_blah.html"),
            os.path.join("cat", "second", "post_2000-03-18_blah.html"),
            os.path.join("cat", "second", "post_2000-03-13_blah.html"),
            os.path.join("cat", "second", "post_2000-03-08_blah.html"),
            os.path.join("cat", "second", "post_2000-03-03_blah.html"),
            os.path.join("cat", "second", "post_2000-02-17_blah.html"),
            os.path.join("cat", "second", "post_2000-02-12_blah.html"),
            os.path.join("cat", "second", "post_2000-02-07_blah.html"),
            os.path.join("cat", "second", "post_2000-02-02_blah.html"),
            os.path.join("cat", "second", "post_2000-01-21_blah.html"),
            os.path.join("cat", "second", "post_2000-01-16_blah.html"),
            os.path.join("cat", "second", "post_2000-01-11_blah.html"),
            os.path.join("cat", "second", "post_2000-01-06_blah.html"),
            os.path.join("cat", "second", "post_2000-01-01_blah.html"),
            ],
          m.GetWriteFileData(m._LEAFNAME))

    def testGeneratePages_3Cats(self):
        """
        More categories: 4 main pages but each category has only 2 pages
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = [ "first", "second", "three" ]
        for x in xrange(0, DEFAULT_ITEMS_PER_PAGE * 3 + 3):
            # x % 3 => we'll generate 3 month pages and we have 3 categories
            # so each category ends up in the same month.
            si = SiteItem(source_item=None,
                          date=datetime(2000, 1 + (x % 3), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=[ cats[x % 3] ])
            items.append(si)

        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            os.path.join("cat", "first", "2000-01.html"),
            os.path.join("cat", "first", "index.html"),
            os.path.join("cat", "first", "atom.xml"),
            os.path.join("cat", "first", "post_2000-01-28_blah.html"),
            os.path.join("cat", "first", "post_2000-01-27_blah.html"),
            os.path.join("cat", "first", "post_2000-01-25_blah.html"),
            os.path.join("cat", "first", "post_2000-01-24_blah.html"),
            os.path.join("cat", "first", "post_2000-01-22_blah.html"),
            os.path.join("cat", "first", "post_2000-01-21_blah.html"),
            os.path.join("cat", "first", "post_2000-01-19_blah.html"),
            os.path.join("cat", "first", "post_2000-01-18_blah.html"),
            os.path.join("cat", "first", "post_2000-01-16_blah.html"),
            os.path.join("cat", "first", "post_2000-01-15_blah.html"),
            os.path.join("cat", "first", "post_2000-01-13_blah.html"),
            os.path.join("cat", "first", "post_2000-01-12_blah.html"),
            os.path.join("cat", "first", "post_2000-01-10_blah.html"),
            os.path.join("cat", "first", "post_2000-01-09_blah.html"),
            os.path.join("cat", "first", "post_2000-01-07_blah.html"),
            os.path.join("cat", "first", "post_2000-01-06_blah.html"),
            os.path.join("cat", "first", "post_2000-01-05_blah.html"),
            os.path.join("cat", "first", "post_2000-01-04_blah.html"),
            os.path.join("cat", "first", "post_2000-01-03_blah.html"),
            os.path.join("cat", "first", "post_2000-01-02_blah.html"),
            os.path.join("cat", "first", "post_2000-01-01_blah.html"),
            os.path.join("cat", "second", "2000-02.html"),
            os.path.join("cat", "second", "index.html"),
            os.path.join("cat", "second", "atom.xml"),
            os.path.join("cat", "second", "post_2000-02-28_blah.html"),
            os.path.join("cat", "second", "post_2000-02-26_blah.html"),
            os.path.join("cat", "second", "post_2000-02-25_blah.html"),
            os.path.join("cat", "second", "post_2000-02-23_blah.html"),
            os.path.join("cat", "second", "post_2000-02-22_blah.html"),
            os.path.join("cat", "second", "post_2000-02-20_blah.html"),
            os.path.join("cat", "second", "post_2000-02-19_blah.html"),
            os.path.join("cat", "second", "post_2000-02-17_blah.html"),
            os.path.join("cat", "second", "post_2000-02-16_blah.html"),
            os.path.join("cat", "second", "post_2000-02-14_blah.html"),
            os.path.join("cat", "second", "post_2000-02-13_blah.html"),
            os.path.join("cat", "second", "post_2000-02-11_blah.html"),
            os.path.join("cat", "second", "post_2000-02-10_blah.html"),
            os.path.join("cat", "second", "post_2000-02-08_blah.html"),
            os.path.join("cat", "second", "post_2000-02-07_blah.html"),
            os.path.join("cat", "second", "post_2000-02-06_blah.html"),
            os.path.join("cat", "second", "post_2000-02-05_blah.html"),
            os.path.join("cat", "second", "post_2000-02-04_blah.html"),
            os.path.join("cat", "second", "post_2000-02-03_blah.html"),
            os.path.join("cat", "second", "post_2000-02-02_blah.html"),
            os.path.join("cat", "second", "post_2000-02-01_blah.html"),
            os.path.join("cat", "three", "2000-03.html"),
            os.path.join("cat", "three", "index.html"),
            os.path.join("cat", "three", "atom.xml"),
            os.path.join("cat", "three", "post_2000-03-27_blah.html"),
            os.path.join("cat", "three", "post_2000-03-26_blah.html"),
            os.path.join("cat", "three", "post_2000-03-24_blah.html"),
            os.path.join("cat", "three", "post_2000-03-23_blah.html"),
            os.path.join("cat", "three", "post_2000-03-21_blah.html"),
            os.path.join("cat", "three", "post_2000-03-20_blah.html"),
            os.path.join("cat", "three", "post_2000-03-18_blah.html"),
            os.path.join("cat", "three", "post_2000-03-17_blah.html"),
            os.path.join("cat", "three", "post_2000-03-15_blah.html"),
            os.path.join("cat", "three", "post_2000-03-14_blah.html"),
            os.path.join("cat", "three", "post_2000-03-12_blah.html"),
            os.path.join("cat", "three", "post_2000-03-11_blah.html"),
            os.path.join("cat", "three", "post_2000-03-09_blah.html"),
            os.path.join("cat", "three", "post_2000-03-08_blah.html"),
            os.path.join("cat", "three", "post_2000-03-07_blah.html"),
            os.path.join("cat", "three", "post_2000-03-06_blah.html"),
            os.path.join("cat", "three", "post_2000-03-05_blah.html"),
            os.path.join("cat", "three", "post_2000-03-04_blah.html"),
            os.path.join("cat", "three", "post_2000-03-03_blah.html"),
            os.path.join("cat", "three", "post_2000-03-02_blah.html"),
            os.path.join("cat", "three", "post_2000-03-01_blah.html"),
            ],
          m.GetWriteFileData(m._LEAFNAME))

    def testGeneratePages_UseCurrMonth(self):
        """
        Test that index contains all items from the first month when
        use_curr_month_in_index is True, even if it's more than
        num_item_page.
        """
        self.sis.use_curr_month_in_index = True
        self.sis.num_item_page = 2
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = []
        # generate 2 months with 5 items per month each
        for mo in xrange(0, 2):
            for d in xrange(0, 5):
                si = SiteItem(source_item=None,
                              date=datetime(2000, 1 + mo, 1 + d, 0, 0, 0),
                              title="blah",
                              permalink="item",
                              content_gen=lambda t, x: "content",
                              categories=cats)
                items.append(si)

        m.GeneratePages(cats, items)

        self.assertListEquals(
          [ "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            "post_2000-02-05_blah.html",
            "post_2000-02-04_blah.html",
            "post_2000-02-03_blah.html",
            "post_2000-02-02_blah.html",
            "post_2000-02-01_blah.html",
            "post_2000-01-05_blah.html",
            "post_2000-01-04_blah.html",
            "post_2000-01-03_blah.html",
            "post_2000-01-02_blah.html",
            "post_2000-01-01_blah.html"
             ],
          m.GetWriteFileData(m._LEAFNAME))

        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertTrue("entries" in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals(
          [ datetime(2000, 2, 5, 0, 0),
            datetime(2000, 2, 4, 0, 0),
            datetime(2000, 2, 3, 0, 0),
            datetime(2000, 2, 2, 0, 0),
            datetime(2000, 2, 1, 0, 0) ],
          [ j.date
            for j in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0]["entries"] ])

        # Now if we set num_item_page to 7, we'll get the 5 items of the last month
        # plus 2 from the next month

        self.sis.num_item_page = 7
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        m.GeneratePages(cats, items)

        self.assertListEquals(
          [ "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            "post_2000-02-05_blah.html",
            "post_2000-02-04_blah.html",
            "post_2000-02-03_blah.html",
            "post_2000-02-02_blah.html",
            "post_2000-02-01_blah.html",
            "post_2000-01-05_blah.html",
            "post_2000-01-04_blah.html",
            "post_2000-01-03_blah.html",
            "post_2000-01-02_blah.html",
            "post_2000-01-01_blah.html"
            ],
          m.GetWriteFileData(m._LEAFNAME))

        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertTrue("entries" in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals(
          [ datetime(2000, 2, 5, 0, 0),
            datetime(2000, 2, 4, 0, 0),
            datetime(2000, 2, 3, 0, 0),
            datetime(2000, 2, 2, 0, 0),
            datetime(2000, 2, 1, 0, 0),
            datetime(2000, 1, 5, 0, 0),
            datetime(2000, 1, 4, 0, 0) ],
          [ j.date
            for j in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0]["entries"] ])

    def testGeneratePages_DontUseCurrMonth(self):
        """
        Test that index contains N max items independantly of the first month when
        use_curr_month_in_index is False.
        """
        self.sis.use_curr_month_in_index = False
        self.sis.num_item_page = 2
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        items = []
        cats = []
        # generate 2 months with 5 items per month each
        for mo in xrange(0, 2):
            for d in xrange(0, 5):
                si = SiteItem(source_item=None,
                              date=datetime(2000, 1 + mo, 1 + d, 0, 0, 0),
                              title="blah",
                              permalink="item",
                              content_gen=lambda t, x: "content",
                              categories=cats)
                items.append(si)

        m.GeneratePages(cats, items)

        self.assertListEquals(
          [ "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            "post_2000-02-05_blah.html",
            "post_2000-02-04_blah.html",
            "post_2000-02-03_blah.html",
            "post_2000-02-02_blah.html",
            "post_2000-02-01_blah.html",
            "post_2000-01-05_blah.html",
            "post_2000-01-04_blah.html",
            "post_2000-01-03_blah.html",
            "post_2000-01-02_blah.html",
            "post_2000-01-01_blah.html"
            ],
          m.GetWriteFileData(m._LEAFNAME))

        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertTrue("entries" in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals(
          [ datetime(2000, 2, 5, 0, 0),
            datetime(2000, 2, 4, 0, 0) ],
          [ j.date
            for j in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0]["entries"] ])

        # Now if we set num_item_page to 7, we'll get the 5 items of the last month
        # plus 2 from the next month

        self.sis.num_item_page = 7
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        m.GeneratePages(cats, items)

        self.assertListEquals(
          [ "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            "post_2000-02-05_blah.html",
            "post_2000-02-04_blah.html",
            "post_2000-02-03_blah.html",
            "post_2000-02-02_blah.html",
            "post_2000-02-01_blah.html",
            "post_2000-01-05_blah.html",
            "post_2000-01-04_blah.html",
            "post_2000-01-03_blah.html",
            "post_2000-01-02_blah.html",
            "post_2000-01-01_blah.html"
            ],
          m.GetWriteFileData(m._LEAFNAME))

        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertTrue("entries" in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals(
          [ datetime(2000, 2, 5, 0, 0),
            datetime(2000, 2, 4, 0, 0),
            datetime(2000, 2, 3, 0, 0),
            datetime(2000, 2, 2, 0, 0),
            datetime(2000, 2, 1, 0, 0),
            datetime(2000, 1, 5, 0, 0),
            datetime(2000, 1, 4, 0, 0) ],
          [ j.date
            for j in m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0]["entries"] ])

    def testClearCache(self):
        """
        Tests the ClearCache method which computes a coherency key and only
        clears the cache when settings or templates change.
        """
        m = MockSiteDefault(self, self.Log(), False, True, self.sis)

        # Start with an empty cache dir and a zero cache clear count.
        # We also need to clear the hash store, which contains the
        # cache coherency key.
        self.RemoveDir(self._cachedir)
        m._hash_store.Clear()
        m.CacheClearCount(reset=True)

        # Check if we need to clear the cache will actually try to clear it
        # since the magic key won't exist in the hash store.
        m._ClearCache(self.sis)
        self.assertEquals(1, m.CacheClearCount(reset=False))

        # Trying to clear again shall do nothing since the parameters have
        # not changed and the key is still in the hash store. This uses the
        # exact same SiteSettings object as earlier.
        m._ClearCache(self.sis)
        self.assertEquals(1, m.CacheClearCount(reset=False))

        # Recompute a new SiteSettings object with exactly the same values
        # and test again. This makes sure the key doesn't depend on objects
        # internal representation which include their pointer (i.e. the
        # default behavior of object.__repr__) or volatile timestamps.
        new_sis, _ = self._computeSisSos()
        m._ClearCache(new_sis)
        self.assertEquals(1, m.CacheClearCount(reset=False))

        # Alter some site setting, this time the cache should get cleared
        # since the old key (still in the hash store) is invalid.
        new_sis.theme = "AnotherTheme"
        m._ClearCache(new_sis)
        self.assertEquals(2, m.CacheClearCount(reset=False))


    def testGenerateItems_Pipeline(self):
        m = MockSiteDefault(self, self.Log(), False, True, self.sis).MakeDestDirs()

        # Disable the cache since we'll call twice the same content
        m._enable_cache = False

        source_dir = os.path.join(self.getTestDataPath(), "album", "blog2", "2007-10-07 11.00_Folder 2")
        source_item = SourceContent(
                date=datetime(2006, 5, 28, 17, 18, 5),
                rel_file=RelFile(source_dir, "Main.blog.izu"),
                title="Title",
                content="""[izu:cat:ignored]
youtube: [youtube:ID:t=12:345x678]
riglink: [link name|riglink:T12896_tiny1.jpg]
rigimg: [img name|rigimg:size:T12896_tiny2.jpg]
innerlink: [To folder 1 in same category|#s:20071007:Folder 1]
crosslink: [To folder 1 in another category|/bar#s:20071007:Folder 1]""",
                tags={ "cat": { "main:": True } },
                source_settings=self.sos)

        # Invoke the real GenerateItem and collect the result
        actual_result = m.GenerateItem(source_item)

        # Now simulate step-by step what GenerateItem does

        test = self
        m.old_GenItem_GetSections = m._GenItem_GetSections

        def Patch_GenItem_GetSections(self, *args):
            sections, tags = self.old_GenItem_GetSections(*args)

            test.assertDictEquals(
                     { "cat": { "main:": True } },
                     tags)
            test.assertListEquals([ "en" ], sections.keys())
            test.assertHtmlEquals(
                   """<span class="izu">
youtube: <object width="345" height="678"> <param name="movie" value="http://www.youtube-nocookie.com/v/ID&hl=en&fs=1&rel=0&color1=0x234900&color2=0x4e9e00&t=12"></param>\n<param name="allowFullScreen" value="true"></param>\n<param name="allowscriptaccess" value="always"></param>\n<embed src="http://www.youtube-nocookie.com/v/ID&hl=en&fs=1&rel=0&color1=0x234900&color2=0x4e9e00" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="345" height="678"></embed>\n</object>
riglink: <a title="link name" href="http://example.com/photos/index.php?album=&img=T12896_tiny1.jpg">link name</a>
rigimg: <img title="img name" src="http://example.com/photos/index.php?th=&album=&img=T12896_tiny2.jpg&sz=size&q=75">
innerlink: <pre> *** curr_category=[[raw locals().get(\'curr_category\', \'NOT-SET2\')]] permalink_url=[[raw locals().get(\'permalink_url\', \'NOT-SET\')]] rel_permalink_url=[[raw locals().get(\'rel_permalink_url\', \'NOT-SET\')]] </pre>
crosslink: <pre> *** curr_category=[[raw locals().get(\'curr_category\', \'NOT-SET2\')]] permalink_url=[[raw locals().get(\'permalink_url\', \'NOT-SET\')]] rel_permalink_url=[[raw locals().get(\'rel_permalink_url\', \'NOT-SET\')]]
</pre></span>""",
                sections["en"])

            return sections, tags

        # use monkey patching to have GenerateItem() invoke the patched method instead
        m._GenItem_GetSections = types.MethodType(Patch_GenItem_GetSections, m, SiteDefault)
        patched_result = m.GenerateItem(source_item)
        self.assertEquals(actual_result, patched_result)

        # GenerateItem() takes a SourceItem and generates a SiteItem
        # which contains a lambda generator
        self.assertEquals(SiteItem, type(actual_result))
        self.assertEquals(type(lambda t, x: None), type(actual_result.content_gen))

        # Generates the pages. We monkey-patch the _WriteFile method to grab
        # whatever would actually get written to disk (and not actually write it)
        data_result = []
        def Patch_WriteFile(self, data, dest_dir, leafname):
            # Do not invoke the old _WriteFile, just append to the result list
            data_result.append(data)

        m._WriteFile = types.MethodType(Patch_WriteFile, m, SiteDefault)
        m.GeneratePages(categories=[ "main", "ignored" ],
                        items=[ actual_result ])

        # We expect 7 files to be written: index + monthly page + single post
        # for the "no-category" main page, plus the same for the actual "main"
        # category folder of the single post, plus one for the empty "ignored"
        # category.
        self.assertEquals(4+3, len(data_result))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
