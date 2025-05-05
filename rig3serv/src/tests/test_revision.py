#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Version

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

import unittest

from tests.rig_test_case import RigTestCase
from rig.version import Version

#------------------------
class VersionTest(RigTestCase):

    def setUp(self):
        self.m = Version()

    def testVersion(self):
        v = self.m.Version()
        self.rigAssertIsInstance(tuple, v)
        self.assertEquals(2, len(v))

    def testVersionString(self):
        v = self.m.VersionString()
        self.assertEquals("%s.%s" % Version.RIG3_VERSION, v)

    @unittest.skip("Not currentyl using SVN")
    def testSvnRevision_Fake(self):
        v = self.m.SvnRevision("$Revision: 42 $")
        self.assertEquals(42, v)

        v = self.m.SvnRevision("$Revision: None $")
        self.assertEquals("Unknown", v)

    @unittest.skip("Not currentyl using SVN")
    def testSvnRevision_Real(self):
        v = self.m.SvnRevision()
        self.rigAssertIsInstance(int, v)
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
