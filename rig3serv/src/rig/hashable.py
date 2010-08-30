#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Base class for a hashable object.

Hashes as computed as md5 using the RigHash method.

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

import sha

#------------------------
class Hashable(object):
    """
    Describe class
    """
    def __init__(self):
        pass

    def RigHash(self, md=None):
        raise NotImplementedError("Object %s should override RigHash" % self.__class__)

    def UpdateHash(self, md, obj):
        if md is None:
            md = sha.new()

        if isinstance(obj, Hashable):
            obj.RigHash(md)

        elif isinstance(obj, (list, tuple)):
            for v in obj:
                self.UpdateHash(md, v)

        elif isinstance(obj, dict):
            for k, v in obj.iteritems():
                self.UpdateHash(md, k)
                self.UpdateHash(md, v)

        elif isinstance(obj, str):
            md.update(str(obj))

        elif isinstance(obj, unicode):
            md.update(unicode(obj))

        else:
            md.update(repr(obj))

        return md

    def __hash__(self):
        return hash(self.RigHash().hexdigest())

    def __cmp__(self, other):
        a = self.RigHash()
        if isinstance(other, Hashable):
            other = other.RigHash()
        return cmp(a, other)

    def __eq__(self, other):
        a = self.RigHash()
        if isinstance(other, Hashable):
            other = other.RigHash()
        return a == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s: hash=%s>" % (self.__class__.__name__, self.RigHash().hexdigest())


#------------------------
class ImmutableHashable(Hashable):
    def __init__(self):
        self._rig_hash = None
        super(ImmutableHashable, self).__init__()

    def RigHash(self, md=None):
        if self._rig_hash is None:
            self._rig_hash = self.RigImmutableHash(md)
        return self._rig_hash

    def RigImmutableHash(self, md=None):
        raise NotImplementedError("Object %s should override RigImmutableHash" % self.__class__)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
