#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re

from rig.template.buffer import Buffer, _WS, _EOL
from rig.template.node import *
from rig.template.tag import *

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
        self._log = log
        self._tags = { "#":   TagComment(),
                       "for": TagFor(),
                       "if":  TagIf() }
        self._filters = { }
        self._InitFileSource(file, source)

    def _InitFileSource(self, file, source):
        _file = file
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
        while not buffer.EndReached():
            n = self._GetNextNode(buffer)
            if n:
                nodes.Append(n)

    def _GetNextNode(self, buffer):
        """
        Returns the next node in the buffer.
        """
        if buffer.StartsWith("[[", consume=True):
            tag = buffer.NextWord().lower()
            parameters = buffer.SkipTo("]]")
            if parameters:
                # strip whitespace and uniformize it, then split by space
                parameters = parameters.strip(_WS + _EOL)
                parameters = re.sub("[%s]+" % (_WS + _EOL), " ", parameters)
                parameters = parameters.split(" ")
            if not buffer.StartsWith("]]", consume=True):
                self._Throw(buffer, "Expected end-tag marker ]]")
            try:
                tag_def = self._tags[tag]
            except KeyError:
                self._Throw(buffer, "Unknown tag %s" % tag)
            content = None
            if tag_def.has_content:
                pass # TODO
            return NodeTag(tag, tag_def, parameters, content)
        else:
            literal = buffer.SkipTo("[[")
            return NodeLiteral(literal)

    def _Throw(self, buffer, msg):
        raise SyntaxError("[%s, line %d, col %d] %s" % (buffer.filename,
                                                   buffer.lineno,
                                                   buffer.offset,
                                                   msg))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
