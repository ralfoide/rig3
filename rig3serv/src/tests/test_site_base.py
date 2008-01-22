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

from rig.site_base import SiteBase
from rig.site_base import DEFAULT_THEME
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir
from rig.source_reader import SourceDirReader

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
        self.assertNotEqual(None, m)
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
        self.assertTrue(os.path.exists(os.path.join(td, "default", "index.html")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", "entry.html")))

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


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
