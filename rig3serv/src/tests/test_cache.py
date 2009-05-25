#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Cache

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import re

from tests.rig_test_case import RigTestCase
from rig.cache import Cache

#------------------------
class CacheTest(RigTestCase):

    def setUp(self):
        self._cachedir = self.MakeTempDir()
        self.m = Cache(self.Log(), self._cachedir)

    def tearDown(self):
        self.m = None
        self.RemoveDir(self._cachedir)

    def testContainsStore(self):
        # Contains returns a tuple (True/False, path).
        c = self.m.Contains("foo")
        self.assertIsInstance(tuple, c)
        self.assertEqual(2, len(c))
        self.assertEqual(False, c[0])
        self.assertMatches("%s.*" % re.escape(self._cachedir), c[1])

        self.m.Store([ "some", "value" ], "foo")

        c = self.m.Contains("foo")
        self.assertIsInstance(tuple, c)
        self.assertEqual(2, len(c))
        self.assertEqual(True, c[0])
        self.assertMatches("%s.*" % re.escape(self._cachedir), c[1])

    def testFindStore(self):
        self.assertEquals(None, self.m.Find("foo"))
        self.m.Store([ "some", "value" ], "foo")
        self.assertListEquals([ "some", "value" ], self.m.Find("foo"))

    def testCounters(self):
        self.assertEquals(0, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(0, self.m._count_write)
        self.assertEquals(0, self.m._count_reused)

        # contains does not affect the counters
        self.m.Contains("foo")

        self.assertEquals(0, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(0, self.m._count_write)
        self.assertEquals(0, self.m._count_reused)

        # generates a miss
        self.m.Find("foo")

        self.assertEquals(1, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(0, self.m._count_write)
        self.assertEquals(0, self.m._count_reused)

        # generates a write
        self.m.Store([ "some", "value" ], "foo")
        self.m.Store([ "some", "value" ], "foo2")

        self.assertEquals(1, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(2, self.m._count_write)
        self.assertEquals(0, self.m._count_reused)

        # generates a read/reuse
        self.m.Find("foo")

        self.assertEquals(1, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(2, self.m._count_write)
        self.assertEquals(1, self.m._count_reused)

        # generates a new read
        self.m.Find("foo2")

        self.assertEquals(1, self.m._count_miss)
        self.assertEquals(0, self.m._count_read)
        self.assertEquals(2, self.m._count_write)
        self.assertEquals(2, self.m._count_reused)

        # Use a fresh cache (to remove the internal memory cache)
        # and read again
        self.m = Cache(self.Log(), self._cachedir)
        self.m.Find("foo")
        self.m.Find("foo2")
        self.assertEquals(0, self.m._count_miss)
        self.assertEquals(2, self.m._count_read)
        self.assertEquals(0, self.m._count_write)
        self.assertEquals(0, self.m._count_reused)

    def testCompute(self):
        self.assertEquals(None, self.m.Find("foo"))

        counter = [ 0 ]
        def inc(c):
            c[0] += 1
            return c

        # Compute, without the cache, executes the lambda
        self.assertListEquals(
              [ "some", "value", [1] ],
              self.m.Compute(
                   key="foo",
                   lambda_expr=lambda : [ "some", "value", inc(counter) ],
                   stat_prefix=None,
                   use_cache=False))

        self.assertEquals(None, self.m.Find("foo"))

        # Compute with cache enabled, executes the lambda and stores
        self.assertListEquals(
              [ "some", "value", [2] ],
              self.m.Compute(
                   key="foo",
                   lambda_expr=lambda : [ "some", "value", inc(counter) ],
                   stat_prefix=None,
                   use_cache=True))

        self.assertListEquals([ "some", "value", [2] ], self.m.Find("foo"))

        # Compute with cache enabled, reloads from cache, does not execute
        # the lambda.
        self.assertListEquals(
              [ "some", "value", [2] ],
              self.m.Compute(
                   key="foo",
                   lambda_expr=lambda : [ "some", "value", inc(counter) ],
                   stat_prefix=None,
                   use_cache=True))

        self.assertListEquals([ "some", "value", [2] ], self.m.Find("foo"))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
