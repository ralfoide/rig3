#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Empty

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
