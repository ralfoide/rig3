#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for HashStore

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

from rig.cache import Cache
from rig.hash_store import HashStore

#------------------------
class HashStoreTest(RigTestCase):

    def setUp(self):
        self._cachedir = self.MakeTempDir()
        self._cache = Cache(self.Log(), self._cachedir)
        self.m = HashStore(self.Log(), self._cache)

    def tearDown(self):
        self.m = None
        self._cache = None
        self.RemoveDir(self._cachedir)

    def testInit(self):
        """
        Test init of HashStore
        """
        self.assertNotEquals(None, self.m)
        self.assertDictEquals({}, self.m._hash_store)

    def testLoad1(self):
        """
        First load should yield and empty cache
        """
        self.assertNotEquals(None, self.m)
        self.assertDictEquals({}, self.m._hash_store)

        self.m.Load()
        self.assertDictEquals({}, self.m._hash_store)

    def testContainsAdd(self):
        self.assertFalse(self.m.Contains("foo"))
        self.m.Add("foo")
        self.assertTrue(self.m.Contains("foo"))

    def testLoadSaveLoad(self):
        """
        Usual use case: load fresh empty store, add something, save, reload.
        """
        # cache dir is fresh empty, so load does nothing
        self.m.Load()
        self.assertFalse(self.m.Contains("foo"))
        self.assertDictEquals({}, self.m._hash_store)

        self.m.Add("foo")
        self.m.Save()

        self.assertTrue(self.m.Contains("foo"))

        # manually erase the store to test loading
        self.m._hash_store = {}
        self.assertDictEquals({}, self.m._hash_store)
        self.m.Load()
        self.assertTrue(self.m.Contains("foo"))



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
