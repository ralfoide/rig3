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

from rig.site.site_default import SiteDefault
from rig.site_base import DEFAULT_THEME
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir
from rig.source_reader import SourceDirReader
from rig.source_item import SourceDir

#------------------------
class MockSiteDefault(SiteDefault):
    """
    Behaves like a SiteDefault() but overrides the base template directory location
    to use testdata/templates instead.
    
    Also traps the last _Filltemplate parameters.
    """
    def __init__(self, test_case, log, dry_run, settings):
        self._test_case = test_case
        self._fill_template_params = {}
        super(MockSiteDefault, self).__init__(log, dry_run, settings)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

    def _FillTemplate(self, template, **keywords):
        """
        Keeps a copy of the _FillTemplate parameters and then call the original.
        Trapped parameters are available in
          self._fill_template_params[template] => keyuword dict.
        """
        self._fill_template_params[template] = dict(keywords)
        return super(MockSiteDefault, self)._FillTemplate(template, **keywords)

#------------------------
class SiteDefaultTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        source = SourceDirReader(self.Log(), None,
                                 os.path.join(self.getTestDataPath(), "album"))
        self.s = SiteSettings(public_name="Test Album",
                              source_list=[ source ],
                              dest_dir=self._tempdir,
                              theme=DEFAULT_THEME,
                              base_url="http://www.example.com",
                              rig_url="http://example.com/photos/")

    def tearDown(self):
        self.RemoveDir(self._tempdir)

    def testSimpleFileName(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc///de\\\\f/g\\h"))
        self.assertEquals("a-ab_12_txt", m._SimpleFileName("a//\\ab!@#$12%^&@&*()_+.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt", maxlen=20))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))

    def testFillTemplate(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        keywords = self.s.AsDict()
        keywords["title"] = "MyTitle"
        keywords["entries"] = ["entry1", "entry2"]
        keywords["last_gen_ts"] = datetime(2007, 11, 12, 14, 15, 16)
        keywords["last_content_ts"] = datetime(2001, 3, 14, 15, 9, 2)
        keywords["rig3_version"] = "3.1.4.15"

        html = m._FillTemplate("index.html", **keywords)
        self.assertIsInstance(str, html)
        self.assertTrue("index.html" in m._fill_template_params)
        self.assertDictEquals(keywords, m._fill_template_params["index.html"])
        self.assertHtmlEquals(
            r"""<html lang="en-US">
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                <title>Test Album - MyTitle</title>
                </head>
                <body>
                entry1
                entry2
                <p>
                Most recent entry: 2001-03-14 15:09:02 --
                Generated on 2007-11-12 14:15:16 by <a href="http://code.google.com/p/rig3/">Rig3 3.1.4.15</a> 
                </body>
                </html>""",
            html)

        keywords = self.s.AsDict()
        keywords["title"] = "MyTitle"
        keywords["sections"] = { "en": "Main <b>Text Content</b> as HTML",
                                 "images": "<a href='page_url'><img href='image_url'/></a>" }
        html = m._FillTemplate("entry.html", **keywords)
        self.assertIsInstance(str, html)
        self.assertTrue("entry.html" in m._fill_template_params)
        self.assertDictEquals(keywords, m._fill_template_params["entry.html"])
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

    def testDateAndTitleFromTitle(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        self.assertEquals((None, "27"),        m._DateAndTitleFromTitle("27"))
        self.assertEquals((None, "2007"),      m._DateAndTitleFromTitle("2007"))
        self.assertEquals((None, "2007-1"),    m._DateAndTitleFromTitle("2007-1"))
        self.assertEquals((None, "2007-10"),   m._DateAndTitleFromTitle("2007-10"))
        self.assertEquals((None, "2007-10-2"), m._DateAndTitleFromTitle("2007-10-2"))
        self.assertEquals((None, "2007102"),   m._DateAndTitleFromTitle("2007102"))
        
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

    def testGenerateItems_Izu(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album")
        item = m.GenerateItem(SourceDir(datetime. RelDir(source_dir, "2007-10-07_Folder 1"), [ "index.izu" ])
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2007, 10, 07), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+</div>', item.content)
        self.assertListEquals([ "foo", "bar", "other" ], item.categories, sort=True)
        self.assertEquals(os.path.join("items", "2007-10-07_Folder-1-index_izu"),
                          item.rel_filename)
    
    def testGenerateItems_Html(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album")
        item = m.GenerateItem(RelDir(source_dir, "2006-05_Movies"), [ "index.html" ])
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2006, 5, 28, 17, 18, 5), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+<!-- \[izu:.+\] --> <table.+>.+</table>.+</div>',
                               item.content)
        self.assertListEquals([ "videos" ], item.categories, sort=True)
        self.assertEquals(os.path.join("items", "2006-05_Movies-index_html"),
                          item.rel_filename)

    def testImgPattern(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
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
        m = MockSiteDefault(self, self.Log(), False, self.s)

        expected = (
            '<a title="2007-11-08 Album Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg">'
            '<img title="Best of 2007" alt="Best of 2007" src="http://example.com/photos/index.php?th=&album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg&sz=400&q=75"/>'
            '</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
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
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
                          "Best of 2007.jpg",
                          -1))

        expected = (
            '<a title="2007-11-08 Album &amp; Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20%26%20Title">'
            '2007-11-08 Album &amp; Title</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album & Title"),
                          None,
                          -1))

    def testGenerateImages(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), []))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "index.izu",
                                                    "index.html",
                                                    "image.jpeg" ]))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "J1234_sound.mp3" ]))
        
        self.assertHtmlEquals(
            m._GetRigLink(RelDir("base", ""), None, -1),
            m._GenerateImages(RelDir("base", ""), [ "J1234.image.jpg" ]))

        self.assertHtmlEquals(
            '<table class="image-table"><tr><td>\n' + m._GetRigLink(RelDir("base", ""), "J1234-image.jpg", -1) + '</td></tr></table>',
            m._GenerateImages(RelDir("base", ""), [ "J1234-image.jpg" ]))

    def testGeneratePageByCategory(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        
        m._GeneratePageByCategory("", "", [], [], [])
        if False:
            # TODO: can't work because of last_gen_ts == today
            self.assertDictEquals(
                  { 'index.html': {
                       'max_page': 1,
                       'prev_url': None,
                       'rig_url': 'http://example.com/photos/',
                       'header_img_url': '',
                       'entries': [],
                       'next_url': None,
                       'last_content_ts': None,
                       'rig3_version': '0.1.0.155',
                       'title': 'All Items',
                       'base_url': 'http://www.example.com',
                       'source_dir': '/home/raphael/workspace/rig3serv/testdata/album',
                       'public_name': 'Test Album',
                       'theme': 'default',
                       'curr_page': 1,
                       'all_categories': [],
                       'dest_dir': '/tmp/tmpcH-IgP',
                       'last_gen_ts': datetime.datetime(2007, 11, 18, 21, 53, 32) } },
                  m._fill_template_params)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
