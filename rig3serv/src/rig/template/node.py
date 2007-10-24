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
    """
    Constructs a list of nodes.
    - list (list [Node]): A list of nodes instances.
    The object can be created with an empty list and nodes can be appended
    later. The list can be empty but should not be None.
    """
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
    """
    Constructs a literal node.
    - literal (string): The literal value of the node, all whitespaces and
      end-lines included.
    """
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
    """
    Constructs a tag node.
    - tag (Tag): A tag definition instance (rig.template.tag.Tag*)
    - parameters (list [str]): List of string parameters. List can be empty
      but not None.
    - content (NodeList): None if this tag does not accept content, otherwise
      must an instance of NodeList (even if it contains only one node inside.)
    """
    def __init__(self, tag, parameters=[], content=None):
        self.tag = tag
        self.parameters = parameters
        self.content = content

    def __eq__(self, rhs):
        if isinstance(rhs, NodeTag):
            return (type(self.tag) == type(rhs.tag) and
                    self.parameters == rhs.parameters and
                    self.content == rhs.content)
        return super(NodeTag, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeTag %s %s %s>" % (self.tag.tag, self.parameters, self.content)


#------------------------
class NodeVariable(Node):
    """
    Constructs a variable node.
    - names (list [str]): A list of name strings that compose the variable.
      The list cannot be empty and must contain at least one string.
    - filter (list [Filter]): A list of filters. The list can be empty but should
      not be None.
    """
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
