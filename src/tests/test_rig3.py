#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rigtestcase import RigTestCase
import rig3

#------------------------
class EmptyTest(RigTestCase):

    def setUp(self):
        self.m = rig3.Rig3()

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of Rig3
        """
        self.assertNotEqual(None, self.m)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
