#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Describes Rig3 internal stats.
"""
__author__ = "ralfoide at gmail com"

from time import time

#------------------------
class _stat(object):
    def __init__(self):
        self.accum = 0
        self.last_start = 0
        self.count = 0


#------------------------
_MAP = {}

def start(key):
    s = _MAP.get(key)
    if s is None:
        s = _MAP[key] = _stat()
    s.last_start = time()

def stop(key):
    s = _MAP.get(key)
    if s is not None and s.last_start:
        s.accum += time() - s.last_start
        s.last_start = 0

def inc(key, n=1):
    s = _MAP.get(key)
    if s is None:
        s = _MAP[key] = _stat()
    s.count += n

#------------------------
def display():
    if not _MAP:
        return
    accum = 0
    for s in _MAP.values():
        accum += s.accum
    print "Total time: %.3f s" % accum
    keys = _MAP.keys()
    keys.sort()
    for k in keys:
        s = _MAP[k]
        print "%-7s: %4d items in %6.2f s" % (k, s.count, s.accum), \
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
