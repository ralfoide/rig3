#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import sys

#------------------------
_WS = " \t\f"
_EOL = "\r\n"

#------------------------
class Buffer(object):
    """
    A buffer wraps a data string with a "current position" offset.
    All operations advance the offset.
    """
    def __init__(self, filename, data, offset=0):
        self.filename = filename
        self.data = data
        self.offset = offset
        self.lineno = 1

    def EndReached(self):
        """
        Returns true if the end of the buffer has been reached
        """
        return self.offset >= len(self.data)

    def StartsWith(self, word, whitespace=False, consume=False):
        """
        Returns true if the given word is present at the current position
        in the buffer.
        If whitespace is true, some whitespace must be present after the word
        or the end of the buffer must have been reached.
        If consume is True, the content is 'consumed' (i.e. offset is moved to end)
        if found. If whitespace is requested, it also consumes the whitespace.
        
        Returns false if the end of the buffer has been reached or if the
        given word is empty.
        """
        if not word or self.EndReached():
            return False
        end = self.offset + len(word)
        if self.data[self.offset:end] == word:
            found = True
            if whitespace and end < len(self.data):
                found = self.data[end] in _WS
                if consume:
                    consume = False
                    while found and self.data[end] in _WS:
                        end += 1
                        self.offset = end
            if consume:
                self.offset = end
            return found
        return False

    def SkipTo(self, word):
        """
        Advances the buffer up to the first occurence of the given word
        (not included) or to the end of the buffer.
        Returns whatever has been read in between or an empty string is
        nothing changed (i.e. if the requested word is already at the current
        location or the end had already been reached or the requested word
        is empty.)
        """
        if not word or self.EndReached():
            return ""
        offset = self.offset
        found = self.data.find(word, offset)
        if found == -1:
            self.offset = len(self.data)
        else:
            self.offset = found
        return self.data[offset:self.offset]
        

    #def SetOffset(self, offset):
    #    self.offset = offset

    def obsolete_NextWord(self):
        """
        Returns None or tuple (string: word, int: initial position)
        Side effect: advances current offset.
        """
        data = self.data
        initial = offset = self.offset
        if self.EndReached():
            return None
        if data[offset:offset + 2] == "[[":
            return ("[[", offset + 2)
        if data[offset:offset + 2] == "]]":
            return ("]]", offset + 2)
        s = ""
        while True:
            if data[offset:offset + 2] in ["[[", "]]"]:
                break
            c = data[offset]
            if c in " \t\f":
                if not s:
                    offset += 1
                    continue
                else:
                    break
            if c in "\r\n":
                self.lineno += 1
            s += c
            offset += 1
        self.offset = offset
        return (s, initial)
        

#------------------------
class Node(object):
    def __init__(self):
        raise NotImplementedError("Abstract class Node cannot be instanciated")

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

class NodeLiteral(Node):
    def __init__(self, literal):
        self.literal = literal

    def __eq__(self, rhs):
        if isinstance(rhs, NodeLiteral):
            return self.literal == rhs.literal
        return super(NodeLiteral, self).__eq__(rhs)

    def __repr__(self):
        return "<NodeLiteral '%s'>" % self.literal

class NodeTag(Node):
    def __init__(self, tag, parameters=[], content=None):
        self.tag = tag
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
class Template(object):
    """
    Parses a template, either from a file or from a string:
    - if file is present, it must be a filename or a file object to be read from.
    - otherwise, source must be defined and it must be a string with the content
      of the template to parse.
    If there's a parsing error, a SyntaxError exception is thrown. 
    If neither file nor source is defined, TypeError is thrown.
    """
    def __init__(self, log, file=None, source=None):
        _file = file
        self._log = log
        if _file is not None:
            if isinstance(_file, str):
                return self._ParseFile(filename=_file)
            elif _file.read:  # does _file.read() exists?
                def _file_name(f):
                    "Returns the filename for a real file() object"
                    try:
                        return f.name
                    except AttributeError:
                        return "file"
                return self._Parse(_file_name(_file), _file.read())
        elif source is not None:
            return self._Parse("source", source)
        raise TypeError("Template: missing file or source parameters")

    def _ParseFile(self, filename):
        """
        Helper to parse a file given by its filename.
        """
        f = None
        try:
            f = file(filename)
            self._Parse(filename, f.read())
        finally:
            if f: f.close()

    def _Parse(self, filename, source):
        """
        Parses a source string for the given filename.
        """
        buffer = Buffer(os.path.basename(filename), source, 0)
        nodes = NodeList()
        self._nodes = nodes
        #while not buffer.EndReached():
        #    n = self._GetNextNode(buffer)
        #    if n:
        #        nodes.Append(n)

    def _GetNextNode(self, buffer):
        """
        Returns the next node in the buffer.
        """
        if buffer.StartsWith("[[", consume=True):
            # get tag
            pass
        else:
            literal = buffer.SkipTo("[[")
            return NodeLiteral(literal)
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
