#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for rig.site.__init__.py (i.e. the mode rig.site)

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

from tests.rig_test_case import RigTestCase
from rig.site import CreateSite
from rig.sites_settings import SiteSettings
from rig.site_base import SiteBase

#------------------------
class CreateSiteTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        self.m = SiteSettings("CreateSiteTest",
                              dest_dir=self._tempdir,
                              cache_dir=self._cachedir)

    def tearDown(self):
        self.m = None
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testCreateSite_Default(self):
        self.assertIsInstance(SiteBase, CreateSite(self.Log(), False, self.m))

    def testCreateSite_Ralf(self):
        self.m.theme = "ralf"
        self.assertIsInstance(SiteBase, CreateSite(self.Log(), False, self.m))

    def testCreateSite_Magic(self):
        self.m.theme = "magic"
        self.assertIsInstance(SiteBase, CreateSite(self.Log(), False, self.m))

    def testCreateSite_Other(self):
        self.m.theme = "bogus theme name"
        self.assertRaises(NotImplementedError, CreateSite, self.Log(), False, self.m)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
