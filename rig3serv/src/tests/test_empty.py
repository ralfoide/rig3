#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Empty

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

from tests.rig_test_case import RigTestCase
from rig.empty import Empty

#------------------------
class EmptyTest(RigTestCase):

    def setUp(self):
        self.m = Empty(self.Log())

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of Empty
        """
        self.assertNotEquals(None, self.m)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
