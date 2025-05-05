#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Settings

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
            [  "expand", "section1", "site1"],
            self.m._parser.sections(),
            sort=True)

        self.assertTrue(self.m._parser.has_section("section1"))
        self.assertTrue(self.m._parser.has_section("site1"))
        self.assertFalse(self.m._parser.has_section("default"))

        # Section1 automatically gets default variables
        self.assertListEquals(
            [ ("key1", "value1"),
              ("global_default_key", "global_value_default") ],
            self.m._parser.items("section1"),
            sort=True)

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

    def testNoExpand(self):
        """
        Test that there is *no* variable expansion
        """
        p = self.getTestDataPath()
        r = self.m.Load(os.path.join(p, "settings_base.rc"))
        self.assertSame(r, self.m)

        self.assertDictEquals(
            { "expanded":     "This variables is expanded to %(global_default_key)s",
              "not_expanded": "This variable is not expanded %(global_default_key)s",
              "global_default_key": "global_value_default" },
            self.m.Items("expand"))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
