#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3

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

import rig3
from rig.log import Log
from rig.sites_settings import SitesSettings

#------------------------
class MockRig3(rig3.Rig3):
    def __init__(self):
        self._usageAndExitCalled = False
        self._ProcessSitesCalled = False
        rig3.Rig3.__init__(self)

    def _UsageAndExit(self, msg=None):
        self._usageAndExitCalled = True

    def ProcessSites(self):
        self._ProcessSitesCalled = True

#------------------------
class Rig3Test(RigTestCase):

    def setUp(self):
        self.m = MockRig3()

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of Rig3
        """
        self.assertNotEquals(None, self.m)

    def testParseArgs_None(self):
        """
        Tests parsing args
        """
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.assertFalse(self.m._dry_run)
        self.m.ParseArgs([ "blah" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.assertFalse(self.m._dry_run)

    def testParseArgs_V(self):
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.m.ParseArgs([ "blah", "-v" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_VERY_VERBOSE)

    def testParseArgs_Q(self):
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.m.ParseArgs([ "blah", "-q" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_MOSLTY_SILENT)

    def testParseArgs_H(self):
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.assertFalse(self.m._usageAndExitCalled)
        self.m.ParseArgs([ "blah", "-h" ])
        self.assertTrue(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)

    def testParseArgs_N(self):
        self.assertFalse(self.m._dry_run)
        self.m.ParseArgs([ "blah", "-n" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertTrue(self.m._dry_run)

    def testParseArgs_F(self):
        self.assertFalse(self.m._force)
        self.m.ParseArgs([ "blah", "-f" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertTrue(self.m._force)

    def testParseArgs_C(self):
        self.assertNotEquals([ "/foo.rc" ], self.m._configPaths)
        self.m.ParseArgs([ "blah", "-c", "/foo.rc" ])
        self.assertListEquals([ "/foo.rc" ], self.m._configPaths)

    def testRun(self):
        """
        Tests run
        """
        self.assertEquals(None, self.m._log)
        self.assertEquals(None, self.m._sites_settings)
        self.assertFalse(self.m._ProcessSitesCalled)
        self.m.Run()
        self.assertIsInstance(Log, self.m._log)
        self.assertIsInstance(SitesSettings, self.m._sites_settings)
        self.assertTrue(self.m._ProcessSitesCalled)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
