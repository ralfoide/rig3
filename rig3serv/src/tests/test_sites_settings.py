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
from rig.sites_settings import SitesSettings, SiteSettings

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
        self.assertEquals("/tmp/data/site1", s.source_dir)
        self.assertEquals("/tmp/generated/site1", s.dest_dir)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
