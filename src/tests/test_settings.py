#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Settings

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rigtestcase import RigTestCase
import rig3
import rig.settings

#------------------------
class SettingsTest(RigTestCase):

    def setUp(self):
        self.m = rig.settings.Settings(self.log())

    def tearDown(self):
        self.m = None

    def testLoadWithDefaults(self):
        """
        Test load of Settings with default paths from Rig3
        """
        r = rig3.Rig3()
        self.m.Load(r._configPaths)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
