#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rigtestcase import RigTestCase
from rig.log import Log
import rig3

#------------------------
class MockRig3(rig3.Rig3):
    def __init__(self):
        self._usageAndExitCalled = False
        rig3.Rig3.__init__(self)

    def _UsageAndExit(self, msg=None):
        self._usageAndExitCalled = True


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
        self.assertNotEqual(None, self.m)

    def testParseArgs(self):
        """
        Tests parsing args
        """
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertFalse(self.m._verbose)
        self.m.ParseArgs([ "blah" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertFalse(self.m._verbose)

        self.m.ParseArgs([ "blah", "-v" ])
        self.assertFalse(self.m._usageAndExitCalled)
        self.assertTrue (self.m._verbose)

        self.m.ParseArgs([ "blah", "-h" ])
        self.assertTrue(self.m._usageAndExitCalled)
        self.assertTrue(self.m._verbose)
        
        self.assertNotEqual([ "/foo.rc" ], self.m._configPaths)
        self.m.ParseArgs([ "blah", "-c", "/foo.rc" ])
        self.assertListEquals([ "/foo.rc" ], self.m._configPaths)

    def testRun(self):
        """
        Tests run
        """
        self.assertEquals(None, self.m._log)
        self.m.Run()
        self.assertIsInstance(Log, self.m._log)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
