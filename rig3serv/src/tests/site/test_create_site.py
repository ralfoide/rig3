#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for rig.site.__init__.py (i.e. the mode rig.site)

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
        self.rigAssertIsInstance(SiteBase, CreateSite(self.Log(), False, True, self.m))

    def testCreateSite_Ralf(self):
        self.m.theme = "ralf"
        self.rigAssertIsInstance(SiteBase, CreateSite(self.Log(), False, True, self.m))

    def testCreateSite_Magic(self):
        self.m.theme = "magic"
        self.rigAssertIsInstance(SiteBase, CreateSite(self.Log(), False, True, self.m))

    def testCreateSite_Other(self):
        self.m.theme = "bogus theme name"
        self.assertRaises(NotImplementedError, CreateSite, self.Log(), False, True, self.m)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
