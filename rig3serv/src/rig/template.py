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

class Buffer(object):
    def __init__(self, filename, data, offset):
        self.filename = filename
        self.data = data
        self.offset = offset
        self.lineno = 1

    def EndReached(self):
        return self.offset >= len(self.data)

    def SetOffset(self, offset):
        self.offset = offset

    def NextWord(self):
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
        

class Node(object): pass

class NodeList(Node):
    def __init__(self, list=[]):
        self.list = list

    def Append(self, node):
        self.list.append(node)

class NodeLiteral(Node):
    def __init__(self, literal):
        self.literal = literal

class NodeTag(Node):
    def __init__(self, tag, parameters=[], content=None):
        self.tag = tag
        self.parameters = parameters
        self.content = content

class NodeVariable(Node):
    def __init__(self, names=[], filters=[]):
        self.names = names
        self.filters = filters

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
                return self._Parse(_file.name and _file.name() or "file",
                                   _file.read())
        elif source is not None:
            return self._Parse("source", source)
        raise TypeError("Template: missing file or source parameters")

    def _ParseFile(self, filename):
        f = None
        try:
            f = file(filename)
            self._Parse(filename, f.read())
        finally:
            if f: f.close()

    def _Parse(self, filename, source):
        buffer = Buffer(os.path.basename(filename), source, 0)
        nodes = NodeList()
        while not buffer.EndReached():
            n = self._GetNextNode(buffer)
            if n:
                nodes.Append(n)
        self._nodes = nodes

    def _GetNextNode(self, buffer):
        word, pos = 
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
