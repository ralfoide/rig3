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

    def testAlbum(self):
        m = Site(self.Log(), "Test Album",
                 os.path.join(self.getTestDataPath(), "album"),
                 os.path.join(self.getTestDataPath(), "dest"),
                 "theme")
        m.Process()


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
