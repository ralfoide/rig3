#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase

import rig.site
from rig.site import Site
from rig.site import DEFAULT_THEME
from rig.dir_parser import DirParser

#------------------------
class SiteTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()

    def tearDown(self):
        self.RemoveDir(self._tempdir)

    def testInit(self):
        """
        Test init of Site
        """
        m = Site(self.Log(), "Site Name", "/tmp/source/data", self._tempdir, DEFAULT_THEME)
        self.assertNotEqual(None, m)
        self.assertEquals("Site Name", m._public_name)
        self.assertEquals("/tmp/source/data", m._source_dir)
        self.assertEquals(self._tempdir, m._dest_dir)
        self.assertEquals(DEFAULT_THEME, m._theme)

    def testPatterns(self):
        self.assertSearch(rig.site._DIR_PATTERN, "2007-10-07_Folder 1")
        self.assertSearch(rig.site._VALID_FILES, "index.izu")
        self.assertSearch(rig.site._VALID_FILES, "image.jpg")
        self.assertSearch(rig.site._VALID_FILES, "image.jpeg")
        self.assertSearch(rig.site._VALID_FILES, "T12896_tiny_jpeg.jpg")

    def testAlbum(self):
        m = Site(self.Log(), "Test Album",
                 os.path.join(self.getTestDataPath(), "album"),
                 self._tempdir,
                 theme=DEFAULT_THEME)
        m.Process()
    
    def testParse(self):
        m = Site(self.Log(), "Test Album",
                 os.path.join(self.getTestDataPath(), "album"),
                 self._tempdir,
                 theme=DEFAULT_THEME)
        p = m.Parse(m._source_dir, m._dest_dir)
        self.assertIsInstance(DirParser, p)
        self.assertListEquals([], p.Files())
        self.assertEquals(1, len(p.SubDirs()))
        self.assertIsInstance(DirParser, p.SubDirs()[0])
        self.assertListEquals([ "index.izu", "T12896_tiny_jpeg.jpg"], p.SubDirs()[0].Files(),
                              sort=True)
        self.assertListEquals([], p.SubDirs()[0].SubDirs())

    def test_SimpleFileName(self):
        m = Site(self.Log(), "Site Name", "/tmp/source/data", self._tempdir, DEFAULT_THEME)
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("ab_12_txt", m._SimpleFileName("ab!@#$12%^&@&*()\\_+/.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt"))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))

    def test_TemplateDir(self):
        m = Site(self.Log(), "Site Name", "/tmp/source/data", self._tempdir, DEFAULT_THEME)
        td = m._TemplateDir()
        self.assertNotEquals("", td)
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        # the templates dir should contain at least the "default" sub-dir
        # with at least the entry.xml and index.xml files
        self.assertTrue(os.path.exists(os.path.join(td, "default")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", "index.xml")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", "entry.xml")))

    def test_FillTemplate(self):
        theme = DEFAULT_THEME
        m = Site(self.Log(), "Site Name", "/tmp/source/data", self._tempdir, theme)
        html = m._FillTemplate(theme, "index.xml", title="MyTitle", entries=["entry1", "entry2"])
        self.assertIsInstance(str, html)
        self.assertEquals("", html)
        
        html = m._FillTemplate(theme, "entry.xml",
                               title="MyTitle",
                               text="Main <b>Text Content</b> as HTML",
                               image="<a href='page_url'><img href='image_url'/></a>")
        self.assertIsInstance(str, html)
        self.assertEquals("", html)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
