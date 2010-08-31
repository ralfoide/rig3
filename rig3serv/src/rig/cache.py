#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Cache storage

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
import sha
import cPickle

from rig import stats

#------------------------
class Cache(object):
    """
    Cache storage for rig3.

    The cache stores Python objects as binary pickle files in the local
    file system cache directory.

    For each object to store, you need a key, which is an Python structure
    (including list, dict, primitives). Computing a key means being able
    to compute a SHA1 of the combined __repr__ of these objects. Computing
    a key can be expensive -- lists and dicts are traversed recursively and
    must NOT contain circular references.

    There are 2 APIs to use the cache:
    - At the lower level:
      - GetKey() to pre-compute a key.
      - Find() checks if the cache has an item, reads it and unpickles it.
      - Store() takes an item, pickes it and store it.
    - At the higher level you have Compute() which does the most common
      operation: check if an item exists and if it does reads it and unpickle
      it. If not, call a lambda to generate the new value and stores it.
    """
    __debug_miss = os.getenv("DEBUG_RIG3_CACHE") is not None

    def __init__(self, log, cache_dir):
        self._log = log
        self._cache_dir = cache_dir
        self._cached = {}
        self._count_read = 0
        self._count_miss = 0
        self._count_write = 0
        self._count_reused = 0
        self._do_reuse = False
        if not cache_dir:
            raise ValueError("Missing cache dir parameter for Cache")

    def SetCacheDir(self, cache_dir):
        self._cache_dir = cache_dir

    def DisplayCounters(self, log):
        """
        Displays some stats about the number of operations done.
        """
        log.Info("Cache: Read %d, Missed %d, Wrote %d, %s %d.",
                 self._count_read,
                 self._count_miss,
                 self._count_write,
                 self._do_reuse and "Reuse" or "No-reuse",
                 self._count_reused)

    def GetKey(self, key):
        """
        Returns the hash for a given key.
        """
        return self._Hash(key)

    def Contains(self, key):
        """
        Returns (True, path) if a cache entry exists for this key.
        Otherwise returns (False, path).
        Does not affect counters.
        """
        h = self._Hash(key)
        p = self._Path(h)
        if os.path.exists(p):
            return True, p
        return False, p

    def Find(self, key):
        """
        Reads some pickle data. Returns None if not found.
        Increments either the miss or read or reused counters.
        """
        found, p = self.Contains(key)
        if found:
            return self._Read(p)
        else:
            self._count_miss += 1
            if Cache.__debug_miss:
                self._log.Debug("Cache Miss: Key=%s", repr(key))
        return None

    def _Read(self, p):
        """
        Internal method to read an entry at the given path "p" and un-pickle it.
        Increments the read counter.
        """
        if self._do_reuse and p in self._cached:
            self._count_reused += 1
            return self._cached[p]

        f = None
        try:
            self._count_read += 1
            f = file(p, "rb")
            content = cPickle.load(f)

            if self._do_reuse:
                self._cached[p] = content

            return content
        finally:
            if f: f.close()

    def Store(self, content, key):
        """
        Stores some data as a pickle.
        Increments the write counter.
        """
        h = self._Hash(key)
        p = self._Path(h)
        self._Write(content, p)

    def _Write(self, content, p):
        """
        Internal helper to store an entry at the given path "p" using a pickle.
        Increments the write counter.
        """
        if self._do_reuse:
            self._cached[p] = content

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
        Does not affect the counters.
        """
        self._RemoveDir(self._cache_dir)
        self._cached = {}

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

        Increments either the (miss + write) counters or the read counter.
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
            if sload:
                sload.Stop()
            return pickled

        if smiss:
            smiss.Stop()
        self._count_miss += 1
        if Cache.__debug_miss:
            self._log.Debug("Cache Miss(%s): Key=%s", stat_prefix, repr(key))

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
        m = sha.new(str(cPickle.HIGHEST_PROTOCOL))
        self._ShaHash(m, key)
        return m.hexdigest()

    def _ShaHash(self, md, obj):
        if isinstance(obj, (list, tuple)):
            for v in obj:
                self._ShaHash(md, v)
        elif isinstance(obj, dict):
            for k, v in obj.iteritems():
                self._ShaHash(md, k)
                self._ShaHash(md, v)
        elif isinstance(obj, unicode):
            # Transforms the unicode string into a python string representation
            # of the unicode string, thus removing encodings.
            md.update(obj.encode("unicode_escape"))
        else:
            try:
                r = repr(obj)
                if "object at 0x" in r:
                    raise AssertionError("Object %s does not override __repr__ for cache hash" % type(obj))
                md.update(r)
            except Exception, e:
                self._log.Debug("Invalid cache object: %s", type(obj))
                raise e

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
            self._log.Exception("RemoveDir '%s' failed: %s", dir_path, e)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
