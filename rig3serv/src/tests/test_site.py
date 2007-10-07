#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase

from rig.site import Site

#------------------------
class SiteTest(RigTestCase):

    def setUp(self):
        self.m = Site(self.Log(), "Site Name", "/tmp/source/data", "/tmp/dest/data", "theme")

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of Site
        """
        self.assertNotEqual(None, self.m)
        self.assertEquals("Site Name", self.m._public_name)
        self.assertEquals("/tmp/source/data", self.m._source_dir)
        self.assertEquals("/tmp/dest/data", self.m._dest_dir)
        self.assertEquals("theme", self.m._theme)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
