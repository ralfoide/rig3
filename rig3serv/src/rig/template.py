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
import sys

#------------------------
_WS = " \t\f"
_EOL = "\r\n"

#------------------------
class Buffer(object):
    """
    A buffer wraps a data string with a "current position" offset.
    All operations advance the offset.
    
    If the offset is 0 and the linesep argument is defined (which defaults
    to os.linesep), then all line separators will be converted to be uniform.
    Set linesep to None if you want to avoid line separator conversion.
    """
    def __init__(self, filename, data, offset=0, linesep=os.linesep):
        self.filename = filename
        self.data = data
        self.offset = offset
        self.lineno = 1
        self.linesep = linesep
        if offset == 0 and linesep:
            self.ConvertLineSep()

    def ConvertLineSep(self, linesep=None):
        """
        This method tries to convert all line endings in the buffer to the
        'default' of the given platform.
        
        The buffer is expected to contain line separators consistent with:
        - only \n, aka unix mode
        - only \r, aka MacOS mode
        - only \r\n pairs, aka DOS/Windows mode
        
        If the linesep argument is defined, it redefines the current Buffer's
        linesep. Otherwise the default (as given to the constructor) is used.
        
        The operation happens in-place to the whole data buffer, independant of the
        current offset position. If offset is not 0, it will raise an exception and
        do nothing since it would ruin the current offset (no attempt is made to fix it).
        
        Returns self (the Buffer) so that you can chain commands.
        """
        if self.offset != 0:
            raise RuntimeError("ConvertLineSep will not apply to buffer with offset=%d" %
                               self.offset)
        if linesep is not None:
            self.linesep = linesep
        sep = ""
        if "\r" in self.data:
            sep = "\r"
            if self.data.find("\r\n") != -1:
                sep = "\r\n"
        elif "\n" in self.data:
            sep = "\n"
        if sep and sep != self.linesep:
            self.data = self.data.replace(sep, self.linesep)
        return self

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
        
        Line numbers: Since this methods will never pass over a line separator,
        it doesn't touch Buffer.lineno
        
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
        
        Line numbers: The method returns *everything* between the current position
        and the first occurence of word, including line separators. If linesep is
        defined, these are scanned for when the buffer is consumed and the
        Buffer.lineno is incremeted as necessary.

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
        result = self.data[offset:self.offset]
        if self.linesep:
            self.lineno += result.count(self.linesep)
        return result

    def NextWord(self):
        """
        Returns the next word in the buffer and consumes it.
        Returns an empty if the end of the buffer has already been reached.
        
        Words are any sequence of characters separated by spaces or line
        separators, or the [[ and ]] tags markers.
        
        Whitespace at the beginning of the buffer's current position is
        consumed and not returned. Whitespace at the end of the word is left
        intact.
        """
        data = self.data
        initial = offset = self.offset
        len_buf = len(data)
        linesep = self.linesep
        len_sep = len(linesep)
        s = ""
        while offset < len_buf:
            if data[offset:offset + 2] in ["[[", "]]"]:
                if not s:
                    offset += 2
                break
            c = data[offset]
            if c in _WS:
                if not s:
                    offset += 1
                    continue
                else:
                    break
            if c == linesep or (len_sep > 1 and data[offset:offset + len_sep] == linesep):
                if not s:
                    offset += len_sep
                    self.lineno += 1
                    continue
                else:
                    break
            s += c
            offset += 1
        self.offset = offset
        return s
        

#------------------------
class Node(object):
    def __init__(self):
        raise NotImplementedError("Abstract class Node cannot be instanciated")

    def __eq__(self, rhs):
        if rhs is None:
            raise RuntimeError("Can't compare %s with None" % repr(self))
        else:
            raise RuntimeError("Can't compare %s with %s" % (repr(self), repr(rhs)))


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
        while not buffer.EndReached():
            n = self._GetNextNode(buffer)
            if n:
                nodes.Append(n)

    def _GetNextNode(self, buffer):
        """
        Returns the next node in the buffer.
        """
        if buffer.StartsWith("[[", consume=True):
            tag = buffer.NextWord()
            parameters = buffer.SkipTo("]]")
            if parameters:
                # strip whitespace and uniformize it, then split by space
                parameters = parameters.strip(_WS + _EOL)
                parameters = re.sub("[%s]+" % (_WS + _EOL), " ", parameters)
                parameters = parameters.split(" ")
            if not buffer.StartsWith("]]", consume=True):
                raise self._Throw(buffer, "Expected end-tag marker ]]")
            content = None
            return NodeTag(tag, parameters, content)
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
