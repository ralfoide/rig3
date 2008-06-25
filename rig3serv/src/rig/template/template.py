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
class _TagEnd(Tag):
    """
    Pseudo-tag to parse end-content [[end]] markers.
    This is used internally, but never in real node tags.
    """
    def __init__(self):
        super(_TagEnd, self).__init__(tag="end", has_content=False)

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
        self._nodes = None
        self._filters = {}
        self.__InitTags()
        self.__InitFileSource(file, source)

    def Generate(self, keywords):
        """
        Generate the template using the parsed content and the given
        keywords, which is a dictionaries of variables to be used by the
        template.
        """
        if self._nodes:
            return self._nodes.Generate(self._log, keywords)
        else:
            return ""

    # ----

    def __InitTags(self):
        self._tags = { "end":  _TagEnd() }
        for tag_def in ALL_TAGS:
            tag = tag_def()
            self._tags[tag.Tag()] = tag

    def __InitFileSource(self, file, source):
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
        self._nodes = self._GetNodeList(buffer, end_expected=False)
        return self
    
    def _GetNodeList(self, buffer, end_expected):
        """
        Parses the buffer for a node list.
        
        If end_expected is true, this is parsing a tag's content and
        expects to find an end-tag marker ([[end]]). It will raise a
        SyntaxError if such a marker is not found in the buffer.
        
        If end_expected is false, this is parsing a full buffer and it
        expects NOT to find such an end-tag marker. It will raise a
        SyntaxError if such a marker is found.
        """
        start_line = buffer.lineno
        start_col = buffer.CurrCol()
        nodes = NodeList()
        while not buffer.EndReached():
            n = self._GetNextNode(buffer)
            if isinstance(n, NodeTag) and isinstance(n.Tag(), _TagEnd):
                if not end_expected:
                    self._SyntaxError(buffer, "[[end]] found but not closing any tag.")
                # end expected and found, return the list of nodes
                return nodes
            nodes.Append(n)
        if end_expected:
            self._SyntaxError(
                buffer,
                "[[end]] not found. " +
                "Opening tag found at line %d, col %d. " % (start_line, start_col) +
                "Did you forget to close a tag?")
        return nodes

    def _GetNextNode(self, buffer):
        """
        Returns the next node in the buffer.
        """
        if buffer.StartsWith("[[", consume=True):
            keyword = buffer.NextWord().lower()
            parameters = buffer.SkipTo("]]")
            if not buffer.StartsWith("]]", consume=True):
                self._SyntaxError(buffer, "Expected end-tag marker ]]")
            try:
                tag_def = self._tags[keyword]
                parameters = parameters.strip(_WS + _EOL)
            except KeyError:
                self._SyntaxError(buffer, "Unknown tag '%s'" % keyword)
            content = None
            if tag_def.HasContent():
                content = self._GetNodeList(buffer, end_expected=True)
            return NodeTag(tag_def, parameters, content)
        else:
            literal = buffer.SkipTo("[[")
            return NodeLiteral(literal)

    def _SyntaxError(self, buffer, msg):
        raise SyntaxError("[%s, line %d, col %d] %s" % (buffer.filename,
                            buffer.lineno,
                            buffer.CurrCol(),
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
