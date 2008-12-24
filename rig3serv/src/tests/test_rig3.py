#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3

Part of Rig3.
License GPL.
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
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.m.ParseArgs([ "blah", "-n" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertEquals(self.m._verbose, Log.LEVEL_NORMAL)
        self.assertTrue(self.m._dry_run)
        
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
