#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Parses Izumi files to HTML

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import sys
from StringIO import StringIO

#------------------------
class _State(object):
    def __init__(self, _file):
        self._file = file
        self._tags = {}
        self._sections = {}

    def Section(self, section):
        return self._sections.get(section, None)

    def StartSection(self, section):
        self._sections[section] = self._sections.get(section, "")
    
    def Append(self, section, content):
        self._sections[section] += content

    def EndsWith(self, section, word):
        return self._sections[section].endsWith(word)

    def EndOfFile(self):
        return self._file is None

    def ReadLine(self):
        """
        Reads a line from the input stream. Strips the end-of-line terminator
        if present.

        If the end of the file has been reached, returns None.
        """
        line = None
        if self._file:
            line = self._file.readline()
            if not line:
                self._file = None
                line = None
            else:
                line = line.strip("\r\n")
        return line

#------------------------
class IzuParser(object):
    """
    Izumi parser.
    This class is stateless.
    """
    def __init__(self, log):
        self._log = log

    def RenderFileToHtml(self, filestream):
        """
        Parses the file 'filename' and return an HTML snippet for it.
        Renders a <div> section, not a full single HTML file.
        
        If source is a string, it is considered a path to be opened as read-only text.
        Otherwise, it must be a file-like object. Use StringIO if you need to parse
        a string buffer.
        
        Returns a tuple:
        - list of izumi header tags (can be an empty list, but not None)
            - most are just srtings. The "cat" (categories) tag is a list of strings. 
        - list of sections.
            - most are HTML content.
            - the "images" section must be a list of RIG urls.
        """
        f = None
        result = None
        try:
            if isinstance(filestream, str):
                f = file(filestream, "rU", 1)  # 1=line buffered, universal
            else:
                f = filestream
            
            state = _State(f)
            self._ParseStream(state)
            result = state.Close()
        except IOError:
            if f and f != filestream:
                f.close()
            self._log.Exception("Read-error for %s" % filestream)
        return result

    def RenderStringToHtml(self, source):
        """
        Renders an Izu source to HTML.
        This is an utility wrapper that actually calls RenderFileToHtml.
        """
        f = StringIO(source)
        return self.RenderFileToHtml(f)

    def _ParseStream(self, state):
        is_comment = False
        curr_section = "en"
        state.StartSection(curr_section)

        while not state.EndOfFile():
            line = state.ReadLine()
            if line is None:
                break
        
            # First take care of the case of comment that opens and close on the same line
            line = re.sub(r"(^|[^!])\[!--.*?--\]", r"\1", line)

            # Now handle the case of a comment that gets closed and another one opened
            # on the line...
            if is_comment:
                m = re.match(".*?--\](?P<line>.*)$", line)
                if m:
                    # A comment is being closed.
                    is_comment = False
                    line = m.group("line") or ""
            if not is_comment:
                m = re.match("(?P<line>.*?(?:^|[^\[]))\[!--.*$", line)
                if m:
                    # A comment has been opened, just use the start of the line
                    is_comment = True
                    line = m.group("line") or ""

            # Bold: __word__
            line = re.sub(r"__(.*?)__", r"<b>\1</b>", line)

            # Italics: ''word''
            line = re.sub(r"''(.*?)''", r"<i>\1</i>", line)
            
            if line:
                append = True
                if line in [ "<br>", "<p>" ]:
                    append = not state.EndsWith(curr_section, line)
                if append:
                    state.Append(curr_section, line)
                

        # end of file reached

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
