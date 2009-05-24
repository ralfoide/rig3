#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Cache storage

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import os
import sys
import md5
import cPickle

from rig import stats

#------------------------
class Cache(object):
    """
    Cache
    """
    def __init__(self, log, cache_dir):
        self._log = log
        self._cache_dir = cache_dir
        self._count_read = 0
        self._count_miss = 0
        self._count_write = 0
        if not cache_dir:
            raise ValueError("Missing cache dir parameter for Cache")

    def DisplayCounters(self, log):
        """
        Displays some stats about the number of operations done.
        """
        log.Info("Cache: Read %d, Missed %d, Wrote %d.",
                 self._count_read, self._count_miss, self._count_write)

    def GetKey(self, key):
        """
        Returns the hash for a given key.
        """
        return self._Hash(key)

    def Contains(self, key):
        """
        Returns (True, path) if a cache entry exists for this key.
        Otherwise returns (False, path).
        """
        h = self._Hash(key)
        p = self._Path(h)
        if os.path.exists(p):
            return True, p
        return False, p


    def Find(self, key):
        """
        Reads some pickle data. Returns None if not found.
        """
        found, p = self.Contains(key)
        if found:
            return self._Read(p)
        else:
            self._count_miss += 1
        return None

    def _Read(self, p):
        """
        Internal method to read an entry at the given path "p" and un-pickle it.
        """
        f = None
        try:
            self._count_read += 1
            f = file(p, "rb")
            return cPickle.load(f)
        finally:
            if f: f.close()


    def Store(self, content, key):
        """
        Stores some data as a pickle.
        """
        h = self._Hash(key)
        p = self._Path(h)
        self._Write(content, p)

    def _Write(self, content, p):
        """
        Internal helper to store an entry at the given path "p" using a pickle.
        """
        if not os.path.exists(p):
            d = os.path.dirname(p)
            if not os.path.exists(d):
                os.makedirs(d, 0777)
        f = None
        try:
            self._count_write += 1
            f = file(p, "wb")
            cPickle.dump(content, f, cPickle.HIGHEST_PROTOCOL)
        finally:
            if f: f.close()

    def Clear(self):
        """
        Empties the cache. The implementation simply removes the
        cache dir recursively if it exists.
        """
        self._RemoveDir(self._cache_dir)

    def Compute(self, key, lambda_expr, stat_prefix=None, use_cache=True):
        """
        Helper method that does the most common operation:
        - If the cache not enabled (use_cache=False) simply run the given
          lambda expression and return its result.
        - If the cache is enabled, tries to find an existing entry, unpickle
          it and return its value. If it is not found, uses the lambda expression
          to compute the value, stores it in the cache and returns the value.
        - If stat_prefix is a string (not None), also updates stat counters
          for load, miss, render and store.
        """

        # Short-circuit when disabling the cache, for testing or experimenting
        if not use_cache:
            s = stat_prefix and stats.Start(stat_prefix + " Render") or None

            result = lambda_expr()
            if s:
                s.Stop()
            return result

        # Using the cache
        sload = stat_prefix and stats.Start(stat_prefix + " Load") or None
        smiss = stat_prefix and stats.Start(stat_prefix + " Miss") or None

        found, p = self.Contains(key)
        if found:
            pickled = self._Read(p)
        else:
            pickled = None
            self._count_miss += 1

        if pickled is not None:
            if sload:
                sload.Stop()
            return pickled

        if smiss:
            smiss.Stop()

        s = stat_prefix and stats.Start(stat_prefix + " Render") or None

        result = lambda_expr()

        if s:
            s.Stop()
        s = stat_prefix and stats.Start(stat_prefix + " Store") or None

        self._Write(result, p)

        if s:
            s.Stop()

        return result


    #----

    def _Path(self, _hash):
        return os.path.join(self._cache_dir, _hash[0:2], _hash)

    def _Hash(self, key):
        m = md5.new(str(cPickle.HIGHEST_PROTOCOL))
        self._Md5Hash(m, key)
        return m.hexdigest()

    def _Md5Hash(self, md, obj):
        if isinstance(obj, (list, tuple)):
            for v in obj:
                self._Md5Hash(md, v)
        elif isinstance(obj, dict):
            for k, v in obj.iteritems():
                self._Md5Hash(md, k)
                self._Md5Hash(md, v)
        else:
            r = repr(obj)
            if "object at 0x" in r:
                raise AssertionError("Object %s does not override __repr__ for cache hash" % type(obj))
            md.update(r)

    def _RemoveDir(self, dir_path):
        """
        Assuming dir_path points to an existing directory, removes all
        files and sub-directories recursively, then removes the actual
        directory itself.

        This is different from os.removedirs() which can only deal with
        *empty* directories :-(
        """
        try:
            if dir_path and os.path.exists(dir_path) and os.path.isdir(dir_path):
                for n in os.listdir(dir_path):
                    p = os.path.join(dir_path, n)
                    if os.path.isdir(p):
                        self._RemoveDir(p)
                    else:
                        os.unlink(p)
                os.rmdir(dir_path)
        except OSError, e:
            self.Log().Exception("RemoveDir '%s' failed: %s", dir_path, e)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
