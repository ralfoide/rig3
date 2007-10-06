#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Settings

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
import rig3
import rig.settings_base

#------------------------
class SettingsBaseTest(RigTestCase):

    def setUp(self):
        self.m = rig.settings_base.SettingsBase(self.log())

    def tearDown(self):
        self.m = None

    def testLoadWithDefaults(self):
        """
        Test load of Settings with default paths from Rig3
        """
        r = rig3.Rig3()
        self.m.Load(r._configPaths)

    def testTestdata(self):
        p = self.getTestDataPath()
        self.m.Load(os.path.join(p, "settings_base.rc"))
        self.assertDictEquals(
            {"global_default_key": "global_value_default"},
            self.m._parser.defaults())
        self.assertListEquals(["section1"], self.m._parser.sections())
        self.assertTrue(self.m._parser.has_section("section1"))
        self.assertListEquals(
            [('key1', 'value1'), ('global_default_key', 'global_value_default')],
            self.m._parser.items("section1"))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
