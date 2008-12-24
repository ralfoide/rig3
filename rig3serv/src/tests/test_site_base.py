#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase

from rig.site_base import SiteBase
from rig.site_base import DEFAULT_THEME
from rig.site.site_default import SiteDefault
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir
from rig.source_reader import SourceDirReader
from rig.source_item import SourceFile, SourceDir, SourceSettings
from rig.parser.dir_parser import RelFile, RelDir

#------------------------
class MockSiteBase(SiteBase):
    """
    Behaves like a Site() but overrides the base template directory location
    to use testdata/templates instead.
    
    Also traps the last _Filltemplate parameters.
    """
    def __init__(self, test_case, log, dry_run, settings):
        self._test_case = test_case
        self._fill_template_params = {}
        super(MockSiteBase, self).__init__(log, dry_run, settings)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

    def GeneratePages(self, categories, items):
        pass

    def GenerateItem(self, source_item):
        return None

class MockSiteBase2(MockSiteBase):
    """
    Like MockSiteBase except GenerateItem is hacked to return its argument.
    Used to test _ProcessSourceItems.
    """
    def __init__(self, test_case, log, dry_run, settings):
        super(MockSiteBase2, self).__init__(test_case, log, dry_run, settings)

    def GenerateItem(self, source_item):
        return source_item

#------------------------
class MockSourceReader(object):
    """
    A mock source reader that returns the list of source items in its
    Parse method. Used to test _ProcessSourceItems.
    """
    def __init__(self, source_items):
        self._source_items = source_items
    
    def Parse(self, dest_dir):
        return self._source_items

#------------------------
class SiteBaseTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        source = SourceDirReader(self.Log(), None,
                                 os.path.join(self.getTestDataPath(), "album"))
        self.s = SiteSettings(public_name="Test Album",
                              source_list=[ source ],
                              dest_dir=self._tempdir,
                              theme=DEFAULT_THEME,
                              base_url="http://www.example.com",
                              rig_base="http://example.com/photos/")

    def tearDown(self):
        self.RemoveDir(self._tempdir)

    def testInit(self):
        """
        Test init of Site
        """
        source = SourceDirReader(self.Log(), None, "/tmp/source/data")
        s = SiteSettings(public_name="Site Name",
                         source_list=[ source ],
                         dest_dir=self._tempdir,
                         theme=DEFAULT_THEME)
        m = MockSiteBase(self, self.Log(), False, s)
        self.assertNotEquals(None, m)
        self.assertEquals("Site Name", m._settings.public_name)
        self.assertEquals(
            [ SourceDirReader(self.Log(), None, "/tmp/source/data") ],
            m._settings.source_list)
        self.assertEquals(self._tempdir, m._settings.dest_dir)
        self.assertEquals(DEFAULT_THEME, m._settings.theme)

    def testPatterns(self):
        self.assertSearch(SiteBase.DIR_PATTERN, "2007-10-07_Folder 1")
        self.assertSearch(SiteBase.DIR_PATTERN, "2006-08-05 20.00.38  Progress")
        self.assertSearch(SiteBase.VALID_FILES, "index.izu")
        self.assertSearch(SiteBase.VALID_FILES, "image.jpg")
        self.assertSearch(SiteBase.VALID_FILES, "image.jpeg")
        self.assertSearch(SiteBase.VALID_FILES, "T12896_tiny_jpeg.jpg")

    def testAlbum(self):
        m = MockSiteBase(self, self.Log(), False, self.s)
        m.Process()

    def testTemplateDir(self):
        m = SiteBase(self.Log(), False, self.s)
        td = m._TemplateDir()
        self.assertNotEquals("", td)
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        # the templates dir should contain at least the "default" sub-dir
        # with at least the entry.xml and index.xml files
        self.assertTrue(os.path.exists(os.path.join(td, "default")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", SiteDefault._TEMPLATE_HTML_INDEX)))
        self.assertTrue(os.path.exists(os.path.join(td, "default", SiteDefault._TEMPLATE_HTML_ENTRY)))

    def testCopyMedia(self):
        m = MockSiteBase(self, self.Log(), False, self.s)
        m._CopyMedia()
        
        self.assertTrue(os.path.isdir (os.path.join(self._tempdir, "media")))
        
        style_css_path = os.path.join(self._tempdir, "media", "style.css")
        self.assertTrue(os.path.exists(style_css_path))
        
        # Check that the style.css has been transformed
        f = file(style_css_path, "rb")
        style_css = f.read()
        f.close()
        self.assertNotSearch("base_url", style_css)
        self.assertNotSearch("public_name", style_css)
        self.assertSearch("base url is http://www.example.com", style_css)
        self.assertSearch("public name is Test Album", style_css)

    def testProcessSourceItems_DuplicatesRemoval(self):
        today = datetime.today()
        source = MockSourceReader(
             [
             SourceFile(today, RelFile("/base", "file1")),
             SourceFile(today, RelFile("/AYB",  "file1")),
             SourceFile(today, RelFile("/AYB",  "file1")),
             SourceFile(today, RelFile("/base", "file2")),
             SourceFile(today, RelFile("/base", "file2")),
             SourceFile(today, RelFile("/base", "file2"),
                               source_settings=SourceSettings(rig_base="/rig/base")),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ]),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ]),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "my", "files" ]),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ]),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ]),
             ])
        m2 = MockSiteBase2(self, self.Log(), False, self.s)

        in_out_items = []
        m2._ProcessSourceItems(source, in_out_items)
        
        self.assertListEquals(
             [
             SourceFile(today, RelFile("/base", "file1")),
             SourceFile(today, RelFile("/AYB",  "file1")),
             SourceFile(today, RelFile("/base", "file2")),
             SourceFile(today, RelFile("/base", "file2"),
                               source_settings=SourceSettings(rig_base="/rig/base")),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ]),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ]),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "my", "files" ]),
             ],
             in_out_items)
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
