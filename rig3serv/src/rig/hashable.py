#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Base class for a hashable object.

Hashes as computed as md5 using the rig_hash method.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import md5
import sys

#------------------------
class Hashable(object):
    """
    Describe class
    """
    def __init__(self):
        pass

    def rig_hash(self, md=None):
        raise NotImplementedError("Object %s should override rig_hash" % self.__class__)

    def update_hash(self, md, obj):
        if md is None:
            md = md5.new()

        if isinstance(obj, Hashable):
            obj.rig_hash(md)

        elif isinstance(obj, (list, tuple)):
            for v in obj:
                self.update_hash(md, v)

        elif isinstance(obj, dict):
            for k, v in obj.iteritems():
                self.update_hash(md, k)
                self.update_hash(md, v)

        elif isinstance(obj, (str, unicode)):
            md.update(str(obj))

        else:
            md.update(repr(obj))

        return md

    def __hash__(self):
        return hash(self.rig_hash().hexdigest())

    def __cmp__(self, other):
        a = self.rig_hash()
        if isinstance(other, Hashable):
            other = other.rig_hash()
        return cmp(a, other)

    def __eq__(self, other):
        a = self.rig_hash()
        if isinstance(other, Hashable):
            other = other.rig_hash()
        return a == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<%s, hash %s>" % (self.__class__, self.rig_hash().hexdigest())

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
