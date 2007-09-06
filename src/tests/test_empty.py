#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Empty

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase
import rig.empty

#------------------------
class EmptyTest(RigTestCase):

    def setUp(self):
        self.m = rig.empty.Empty()

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of Empty
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
