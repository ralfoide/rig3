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

#------------------------
class Cache(object):
    """
    Cache
    """
    def __init__(self, log, cache_dir):
        self._log = log
        self._cache_dir = cache_dir
        if not cache_dir:
            raise ValueError("Missing cache dir parameter for Cache")

    def Contains(self, key):
        h = self._Hash(key)
        p = self._Path(h)
        if os.path.exists(p):
            #self._log.Debug("Cache contains %s", p)
            return p
        #self._log.Debug("Cache does NOT contain %s", p)
        return None

    def Find(self, key):
        """
        Reads some pickle data. Returns None if not found.
        """
        p = self.Contains(key)
        if p:
            f = None
            try:
                f = file(p, "rb")
                #self._log.Debug("Cache find/load %s", p)
                return cPickle.load(f)
            finally:
                if f: f.close()
        return None

    def Store(self, content, key):
        """
        Stores some data as a pickle.
        """
        h = self._Hash(key)
        p = self._Path(h)
        if not os.path.exists(p):
            d = os.path.dirname(p)
            if not os.path.exists(d):
                os.makedirs(d, 0777)
        f = None
        try:
            #self._log.Debug("Cache store %s", p)
            f = file(p, "wb")
            cPickle.dump(content, f, cPickle.HIGHEST_PROTOCOL)
        finally:
            if f: f.close()

    def Clear(self):
        """
        Empties the cache. The implementation simply removes the
        cache dir if it exists.
        """
        self._RemoveDir(self._cache_dir)

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
