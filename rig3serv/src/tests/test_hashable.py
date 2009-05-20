#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Hashable

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import md5
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

    def assertMd5Equals(self, expected, actual, msg=None):
        """
        Helper for testing MD5 equality
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

        # The md5 is not really an object so we can't quite test its type
        # using isinstance(). Check the value directly then.
        # I.e. we can't write this: self.assertIsInstance(md5, h)
        self.assertMd5Equals(md5.new("blah"), h)

    def testRigHashes(self):
        """
        Test various hashes on complex structures.
        """

        m = md5.new("some string")
        self.assertMd5Equals(m,
              MyHash("some string").RigHash())

        m = md5.new()
        m.update("some")
        m.update(" string")
        self.assertMd5Equals(m,
              MyHash([ "some", " string" ]).RigHash())

        m = md5.new()
        m.update("1")
        m.update("one")
        m.update("2")
        m.update("two")
        m.update("3")
        m.update("4"),
        self.assertMd5Equals(m,
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
