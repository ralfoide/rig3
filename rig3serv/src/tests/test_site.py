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
from rig.dir_parser import DirParser

#------------------------
class SiteTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInit(self):
        """
        Test init of Site
        """
        m = Site(self.Log(), "Site Name", "/tmp/source/data", "/tmp/dest/data", "theme")
        self.assertNotEqual(None, m)
        self.assertEquals("Site Name", m._public_name)
        self.assertEquals("/tmp/source/data", m._source_dir)
        self.assertEquals("/tmp/dest/data", m._dest_dir)
        self.assertEquals("theme", m._theme)

    def testPatterns(self):
        self.assertSearch(rig.site._DIR_PATTERN, "2007-10-07_Folder 1")
        self.assertSearch(rig.site._VALID_FILES, "index.izu")
        self.assertSearch(rig.site._VALID_FILES, "image.jpg")
        self.assertSearch(rig.site._VALID_FILES, "image.jpeg")
        self.assertSearch(rig.site._VALID_FILES, "T12896_tiny_jpeg.jpg")

    def testAlbum(self):
        m = Site(self.Log(), "Test Album",
                 os.path.join(self.getTestDataPath(), "album"),
                 os.path.join(self.getTestDataPath(), "dest"),
                 "theme")
        m.Process()
    
    def testParse(self):
        m = Site(self.Log(), "Test Album",
                 os.path.join(self.getTestDataPath(), "album"),
                 os.path.join(self.getTestDataPath(), "dest"),
                 "theme")
        p = m.Parse(m._source_dir, m._dest_dir)
        self.assertIsInstance(DirParser, p)
        self.assertListEquals([], p.Files())
        self.assertEquals(1, len(p.SubDirs()))
        self.assertIsInstance(DirParser, p.SubDirs()[0])
        self.assertListEquals([ "index.izu", "T12896_tiny_jpeg.jpg"], p.SubDirs()[0].Files(),
                              sort=True)
        self.assertListEquals([], p.SubDirs()[0].SubDirs())

    def testSimpleFileName(self):
        m = Site(self.Log(), "Site Name", "/tmp/source/data", "/tmp/dest/data", "theme")
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("ab_12_txt", m._SimpleFileName("ab!@#$12%^&@&*()\\_+/.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt"))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
