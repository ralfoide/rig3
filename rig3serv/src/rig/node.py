#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"


#------------------------
class Node(object):
    def __init__(self):
        raise NotImplementedError("Abstract class Node cannot be instanciated")

    def __eq__(self, rhs):
        if rhs is None:
            raise RuntimeError("Can't compare %s with None" % repr(self))
        else:
            raise RuntimeError("Can't compare %s with %s" % (repr(self), repr(rhs)))


#------------------------
class NodeList(Node):
    def __init__(self, list=[]):
        self.list = list

    def Append(self, node):
        self.list.append(node)

    def __eq__(self, rhs):
        if isinstance(rhs, NodeList):
            return self.list == rhs.list
        return super(NodeList, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeList %s>" % (self.list)


#------------------------
class NodeLiteral(Node):
    def __init__(self, literal):
        self.literal = literal

    def __eq__(self, rhs):
        if isinstance(rhs, NodeLiteral):
            return self.literal == rhs.literal
        return super(NodeLiteral, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeLiteral '%s'>" % self.literal


#------------------------
class NodeTag(Node):
    def __init__(self, tag, tag_def, parameters=[], content=None):
        self.tag = tag
        self.tag_def = tag_def
        self.parameters = parameters
        self.content = content

    def __eq__(self, rhs):
        if isinstance(rhs, NodeTag):
            return (self.tag == rhs.tag and
                    self.parameters == rhs.parameters and
                    self.content == rhs.content)
        return super(NodeTag, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeTag %s %s %s>" % (self.tag, self.parameters, self.content)


#------------------------
class NodeVariable(Node):
    def __init__(self, names=[], filters=[]):
        self.names = names
        self.filters = filters

    def __eq__(self, rhs):
        if isinstance(rhs, NodeVariable):
            return (self.names == rhs.names and
                    self.filters == rhs.filters )
        return super(NodeVariable, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeVar %s %s>" % (self.names, self.filters)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
