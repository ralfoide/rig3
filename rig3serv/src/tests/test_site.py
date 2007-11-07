#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase

import rig.site
from rig.site import Site
from rig.site import DEFAULT_THEME, _IMG_PATTERN
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser

#------------------------
class MockSite(Site):
    """
    Behaves like a Site() but overrides the base template directory location
    to use testdata/templates instead.
    """
    def __init__(self, test_case, log, dry_run, settings):
        self._test_case = test_case
        super(MockSite, self).__init__(log, dry_run, settings)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

#------------------------
class SiteTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self.s = SiteSettings(public_name="Test Album",
                              source_dir=os.path.join(self.getTestDataPath(), "album"),
                              dest_dir=self._tempdir,
                              theme=DEFAULT_THEME)

    def tearDown(self):
        self.RemoveDir(self._tempdir)

    def testInit(self):
        """
        Test init of Site
        """
        s = SiteSettings(public_name="Site Name",
                         source_dir="/tmp/source/data",
                         dest_dir=self._tempdir,
                         theme=DEFAULT_THEME)
        m = Site(self.Log(), False, s)
        self.assertNotEqual(None, m)
        self.assertEquals("Site Name", m._public_name)
        self.assertEquals("/tmp/source/data", m._source_dir)
        self.assertEquals(self._tempdir, m._dest_dir)
        self.assertEquals(DEFAULT_THEME, m._theme)

    def testPatterns(self):
        self.assertSearch(rig.site._DIR_PATTERN, "2007-10-07_Folder 1")
        self.assertSearch(rig.site._DIR_PATTERN, "2006-08-05 20.00.38  Progress")
        self.assertSearch(rig.site._VALID_FILES, "index.izu")
        self.assertSearch(rig.site._VALID_FILES, "image.jpg")
        self.assertSearch(rig.site._VALID_FILES, "image.jpeg")
        self.assertSearch(rig.site._VALID_FILES, "T12896_tiny_jpeg.jpg")

    def testAlbum(self):
        m = Site(self.Log(), False, self.s)
        m.Process()
    
    def testParse(self):
        m = Site(self.Log(), False, self.s)
        p = m._Parse(m._source_dir, m._dest_dir)
        self.assertIsInstance(DirParser, p)
        self.assertListEquals([], p.Files())
        self.assertEquals(3, len(p.SubDirs()))
        self.assertIsInstance(DirParser, p.SubDirs()[0])
        self.assertIsInstance(DirParser, p.SubDirs()[1])
        self.assertIsInstance(DirParser, p.SubDirs()[2])
        self.assertEquals("2006-05_Movies", p.SubDirs()[0]._rel_curr_dest_dir)
        self.assertEquals("2006-08-05 20.00.38  Progress", p.SubDirs()[1]._rel_curr_dest_dir)
        self.assertEquals("2007-10-07_Folder 1", p.SubDirs()[2]._rel_curr_dest_dir)
        self.assertListEquals([ "index.html"], p.SubDirs()[0].Files())
        self.assertListEquals([ "index.html"], p.SubDirs()[1].Files())
        self.assertListEquals([ "T12896_tiny_jpeg.jpg", "index.izu"], p.SubDirs()[2].Files())
        self.assertListEquals([], p.SubDirs()[0].SubDirs())
        self.assertListEquals([], p.SubDirs()[1].SubDirs())
        self.assertListEquals([], p.SubDirs()[2].SubDirs())

    def testSimpleFileName(self):
        m = Site(self.Log(), False, self.s)
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc///de\\\\f/g\\h"))
        self.assertEquals("a-ab_12_txt", m._SimpleFileName("a//\\ab!@#$12%^&@&*()_+.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt", maxlen=20))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))

    def testTemplateDir(self):
        m = Site(self.Log(), False, self.s)
        td = m._TemplateDir()
        self.assertNotEquals("", td)
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        # the templates dir should contain at least the "default" sub-dir
        # with at least the entry.xml and index.xml files
        self.assertTrue(os.path.exists(os.path.join(td, "default")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", "index.html")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", "entry.html")))

    def testFillTemplate(self):
        m = MockSite(self, self.Log(), False, self.s)
        html = m._FillTemplate(self.s.theme, "index.html", title="MyTitle", entries=["entry1", "entry2"])
        self.assertIsInstance(str, html)
        self.assertHtmlEquals(
            r"""<html lang="en-US">
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                <title>MyTitle</title>
                </head>
                <body>
                entry1
                entry2
                </body>
                </html>""",
            html)

        keywords = { "title": "MyTitle",
                     "sections": { "en": "Main <b>Text Content</b> as HTML",
                                   "images": "<a href='page_url'><img href='image_url'/></a>" } }
        html = m._FillTemplate(self.s.theme, "entry.html", **keywords)
        self.assertIsInstance(str, html)
        self.assertHtmlEquals(
            r"""<div class="entry">
                <h2>MyTitle</h2>
                Main <b>Text Content</b> as HTML
                <br/>
                <a href='page_url'><img href='image_url'/></a>
                <br/>
                </div>
                """,
            html)

    def testDateFromTitle(self):
        m = Site(self.Log(), False, self.s)

        self.assertEquals(None, m._DateFromTitle("27"))
        self.assertEquals(None, m._DateFromTitle("2007"))
        self.assertEquals(None, m._DateFromTitle("2007-1"))
        self.assertEquals(None, m._DateFromTitle("2007-10"))
        self.assertEquals(None, m._DateFromTitle("2007-10-2"))
        self.assertEquals(None, m._DateFromTitle("2007102"))
        
        self.assertEquals(datetime(2007, 10, 27), m._DateFromTitle("20071027"))
        self.assertEquals(datetime(2007, 10, 27), m._DateFromTitle("2007-10-27"))
        self.assertEquals(datetime(2007, 10, 27), m._DateFromTitle("2007/10/27"))
        self.assertEquals(datetime(2007, 10, 27), m._DateFromTitle("2007-10/27"))
        self.assertEquals(datetime(2007, 10, 27, 12, 13, 14), m._DateFromTitle("20071027121314"))
        self.assertEquals(datetime(2007, 10, 27, 12, 13, 14), m._DateFromTitle("2007-10-27-12-13-14"))
        self.assertEquals(datetime(2007, 10, 27, 12, 13, 14), m._DateFromTitle("2007-10-27 12-13-14"))
        self.assertEquals(datetime(2007, 10, 27, 12, 13, 14), m._DateFromTitle("2007/10/27 12:13:14"))
        self.assertEquals(datetime(2007, 10, 27, 12, 13, 14), m._DateFromTitle("2007-10/27,12/13/14"))

    def testCopyMedia(self):
        m = MockSite(self, self.Log(), False, self.s)
        m._CopyMedia()
        self.assertTrue(os.path.isdir (os.path.join(self._tempdir, "media")))
        self.assertTrue(os.path.exists(os.path.join(self._tempdir, "media", "style.css")))
    
    def testGenerateItems_Izu(self):
        m = MockSite(self, self.Log(), False, self.s)
        m._MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album", "2007-10-07_Folder 1")
        item = m._GenerateItem(source_dir, "2007-10-07_Folder 1", [ "index.izu" ])
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2007, 10, 07), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+</div>', item.content)
        self.assertListEquals([], item.categories)
        self.assertEquals(os.path.join("items", "2007-10-07_Folder-1-index_izu"),
                          item.rel_filename)
    
    def testGenerateItems_Html(self):
        m = MockSite(self, self.Log(), False, self.s)
        m._MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album", "2006-05_Movies")
        item = m._GenerateItem(source_dir, "2006-05_Movies", [ "index.html" ])
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2006, 5, 28, 17, 18, 5), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+<!-- \[izu:.+\] --> <table.+>.+</table>.+</div>',
                               item.content)
        self.assertListEquals([], item.categories)
        self.assertEquals(os.path.join("items", "2006-05_Movies-index_html"),
                          item.rel_filename)

    def testImgPattern(self):
        self.assertEquals(None, _IMG_PATTERN.match("myimage.jpg"))
        self.assertEquals(None, _IMG_PATTERN.match("PICT1200.jpg"))
        self.assertEquals(None, _IMG_PATTERN.match("R12345-Some Name.bmp"))
        self.assertEquals(None, _IMG_PATTERN.match("R12345-Some Name.gif"))
        self.assertDictEquals({ "index": "1000",
                                "rating": "_",
                                "name": " Old Index ",
                                "ext": ".jpg" }, 
                              _IMG_PATTERN.match("1000_ Old Index .jpg").groupdict())
        self.assertDictEquals({ "index": "R12345",
                                "rating": "_",
                                "name": "Some Name",
                                "ext": ".jpg" }, 
                              _IMG_PATTERN.match("R12345_Some Name.jpg").groupdict())
        self.assertDictEquals({ "index": "X12345",
                                "rating": "-",
                                "name": "Some Movie",
                                "ext": ".original.mov" }, 
                              _IMG_PATTERN.match("X12345-Some Movie.original.mov").groupdict())
        self.assertDictEquals({ "index": "Y31415",
                                "rating": "+",
                                "name": "Web Version",
                                "ext": ".web.mov" }, 
                              _IMG_PATTERN.match("Y31415+Web Version.web.mov").groupdict())
        self.assertDictEquals({ "index": "Z31415",
                                "rating": ".",
                                "name": "Web Version",
                                "ext": ".web.wmv" }, 
                              _IMG_PATTERN.match("Z31415.Web Version.web.wmv").groupdict())

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
