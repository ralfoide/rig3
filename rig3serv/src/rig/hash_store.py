#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Hash storage

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

from rig.cache import Cache

#------------------------
class HashStore(object):
    """
    Hash storage for rig3.

    The "hash store" is a list of key hashes with no values that is stored
    between runs of rig3. Typically one run will compute a bunch of items
    and the next run will want to know if items are new: just store hashes
    in the hash store and check for their presence at the next run. This
    is useful only when the value is not relevant (and needs not be stored.)

    Keys should be strings or anything that can be a key in a dictionary.
    They don't have to be MD5 hashes however it would be best to keep them
    short since there are stored in the cache.

    The bottom line is that storing md5 hashes is the original intent,
    typically some computed using rig.Cache.GetKey().
    """
    def __init__(self, log, cache):
        self._log = log
        self._cache = cache
        self._hash_store = {}

    def Load(self):
        self._hash_store = self._cache.Compute(
             key=str(self.__class__) + "_hash_store",
             lambda_expr=lambda : self._hash_store,
             stat_prefix=None,
             use_cache=True)

    def Save(self):
        key=str(self.__class__) + "_hash_store"
        self._cache.Store(self._hash_store, key)

    def Contains(self, key):
        return key in self._hash_store

    def Add(self, key):
        self._hash_store[key] = 1


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
