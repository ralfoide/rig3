#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Describes Rig3 internal stats.

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
def Display(log):
    if not _MAP:
        return
    keys = _MAP.keys()
    keys.sort()
    key_len = 0
    for k in keys:
        key_len = max(key_len, len(k))
    for k in keys:
        s = _MAP[k]
        log.Info("%-*s: %4d items in %6.2f s%s",
                 key_len,
                 k,
                 s.count,
                 s.accum,
                 s.count > 1 and (" (%6.2f ms/item)" % (1000.0 * s.accum / s.count)) or "")

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
