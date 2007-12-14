#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Version

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase
from rig.version import Version

#------------------------
class VersionTest(RigTestCase):

    def setUp(self):
        self.m = Version()

    def testVersion(self):
        v = self.m.Version()
        self.assertIsInstance(tuple, v)
        self.assertEquals(2, len(v))

    def testVersionString(self):
        v = self.m.VersionString()
        self.assertEquals("%s.%s" % Version.RIG3_VERSION, v)

    def testSvnRevision_Fake(self):
        v = self.m.SvnRevision("$Revision: 42 $")
        self.assertEquals(42, v)
        
        v = self.m.SvnRevision("$Revision: None $")
        self.assertEquals("Unknown", v)        

    def testSvnRevision_Real(self):
        v = self.m.SvnRevision()
        self.assertIsInstance(int, v)
        self.assertTrue(v > 150)
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
