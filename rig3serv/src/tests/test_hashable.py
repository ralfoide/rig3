#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Hashable

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

import sha
from tests.rig_test_case import RigTestCase
from rig.hashable import Hashable

#------------------------
class MyHash(Hashable):

    def __init__(self, value):
        super(MyHash, self).__init__()
        self._value = value

    def RigHash(self, md=None):
        md = self.UpdateHash(md, self._value)
        return md


#------------------------
class HashableTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def assertShaEquals(self, expected, actual, msg=None):
        """
        Helper for testing SHA1 equality
        """
        self.assertEquals(expected.hexdigest(), actual.hexdigest(), msg)

    def testNeedsOverride(self):
        """
        Test that Hashable.RigHash raises an error if not overridden
        """
        try:
            m = Hashable()
            m.RigHash()
        except NotImplementedError, e:
            self.assertEquals(
                  "Object <class 'rig.hashable.Hashable'> should override RigHash",
                  str(e))
            return
        self.fail("Hashable.RigHash() failed to raise an error when not overridden")

    def testOverrideWorks(self):
        """
        Tests that overriding Hashable.RigHash doesn't raise an exception and
        returns the expected value
        """
        m = MyHash("blah")
        h = m.RigHash()

        # The sha is not really an object so we can't quite test its type
        # using isinstance(). Check the value directly then.
        # I.e. we can't write this: self.rigAssertIsInstance(sha, h)
        self.assertShaEquals(sha.new("blah"), h)

    def testRigHashes(self):
        """
        Test various hashes on complex structures.
        """

        m = sha.new("some string")
        self.assertShaEquals(m,
              MyHash("some string").RigHash())

        m = sha.new()
        m.update("some")
        m.update(" string")
        self.assertShaEquals(m,
              MyHash([ "some", " string" ]).RigHash())

        m = sha.new()
        m.update("1")
        m.update("one")
        m.update("2")
        m.update("two")
        m.update("3")
        m.update("4"),
        self.assertShaEquals(m,
              MyHash({ 1: "one", 2: "two", 3: 4 }).RigHash())


#------------------------


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
