#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Describes Rig3 internal stats.
"""
__author__ = "ralfoide at gmail com"

from time import time

#------------------------
class Stat(object):
    def __init__(self):
        self.accum = 0
        self.last_start = 0
        self.count = 0

    def Start(self):
        self.last_start = time()
        return self

    def Stop(self, n=1):
        self.count += n
        if self.last_start:
            self.accum += time() - self.last_start
            self.last_start = 0
        return self


#------------------------
_MAP = {}

def Start(key):
    s = _MAP.get(key)
    if s is None:
        s = _MAP[key] = Stat()
    s.Start()
    return s

def Stop(key, n=1):
    s = _MAP.get(key)
    if s is not None:
        s.Stop(n)
    return s

#------------------------
def Display():
    if not _MAP:
        return
    keys = _MAP.keys()
    keys.sort()
    key_len = 0
    for k in keys:
        key_len = max(key_len, len(k))
    for k in keys:
        s = _MAP[k]
        print "%-*s: %4d items in %6.2f s" % (key_len, k, s.count, s.accum), \
              s.count > 1 and (" (%6.2f ms/item)" % (1000.0 * s.accum / s.count)) or ""

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
