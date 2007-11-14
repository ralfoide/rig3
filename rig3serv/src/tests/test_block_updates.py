#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase

#------------------------
class BlockUpdatesTest(RigTestCase):

    def testInit(self):
        """
        When the fail() action is present, it fails unit tests and thus
        prevent prod sites from automatically updating and picking up the
        new checkout.
        """
        #self.fail("This voluntarily blocks automatic updates")
        pass


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
