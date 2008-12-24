#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Settings

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import os

import rig3
from tests.rig_test_case import RigTestCase
from rig.settings_base import SettingsBase

#------------------------
class SettingsBaseTest(RigTestCase):

    def setUp(self):
        self.m = SettingsBase(self.Log())

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
        r = self.m.Load(os.path.join(p, "settings_base.rc"))
        self.assertSame(r, self.m)

        # SettingsBase.ConfigParser() is like self._parser
        self.assertSame(self.m._parser, self.m.ConfigParser()) 

        # Default variables, inherited by all sections
        self.assertDictEquals(
            {"global_default_key": "global_value_default"},
            self.m._parser.defaults())

        # Defined sections... the default one is not present
        self.assertListEquals(
            [ "section1", "site1" ],
            self.m._parser.sections())

        self.assertTrue(self.m._parser.has_section("section1"))
        self.assertTrue(self.m._parser.has_section("site1"))
        self.assertFalse(self.m._parser.has_section("default"))

        # Section1 automatically gets default variables
        self.assertListEquals(
            [ ("key1", "value1"),
              ("global_default_key", "global_value_default") ],
            self.m._parser.items("section1"))
        
        # The settings_base.rc file entry for [site1] has multiple definitions
        # for the same variable. Only the last definition is used. 
        self.assertListEquals(
            [ ("sources", "/tmp/data/site1/last"),
              ("global_default_key", "global_value_default") ],
            self.m._parser.items("site1"),
            sort=True)

        # SettingsBase.Items() returns the items as a dictionnary
        # instead of a list of tuples.
        self.assertDictEquals(
            { "sources": "/tmp/data/site1/last",
              "global_default_key": "global_value_default" },
            self.m.Items("site1"))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
