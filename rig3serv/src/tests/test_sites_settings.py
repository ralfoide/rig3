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
import rig.sites_settings

#------------------------
class SitesSettingsTest(RigTestCase):

    def setUp(self):
        self.m = rig.sites_settings.SitesSettings(self.log())

    def tearDown(self):
        self.m = None

    def testTestdata(self):
        p = self.getTestDataPath()
        self.m.Load(os.path.join(p, "sites_settings.rc"))
        self.assertListEquals(["site1", "site2"], self.m.Sites())

        self.assertEquals("blue_template", self.m.Theme("site1"))
        self.assertEquals("Site 1", self.m.PublicName("site1"))
        self.assertEquals("/tmp/data/site1", self.m.SourceDir("site1"))
        self.assertEquals("/tmp/generated/site1", self.m.DestDir("site1"))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
