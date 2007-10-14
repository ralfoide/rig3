#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Parses Izumi files to HTML

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import sys

#------------------------
class _State(object):
    def __init__(self):
        self.html = ""
        self.images = []
        self.tags = []
        self.cats = []

#------------------------
class IzuParser(object):
    """
    Izumi parser.
    This class is stateless.
    """
    def __init__(self, log):
        self._log = log

    def RenderFileToHtml(self, source):
        """
        Parses the file 'source' and return an HTML snippet for it.
        Renders a <div> section, not a full single HTML file.
        
        If source is a string, it is considered a path to be opened as read-only text.
        Otherwise, it must be a file-like object. Use StringIO if you need to parse
        a string buffer.
        
        Returns a tuple:
        - the html itself
        - list of izumi header tags (can be an empty list, but not None)
        - list of categories defined by the izumi header (can be an empty list, but not None)
        - list of referenced images (can be an empty list, but not None)
        """
        f = None
        result = ("", [], [], [])
        try:
            if isinstance(source, str):
                f = file(source, "r", 1)  # 1=line buffered
            else:
                f = source
            state = self._InitState()
            # file.readline returns each line with its line ending and returns an empty string
            # when the end of the file has been reached
            l = f.readline()
            while l:
                self._ProcessLine(state, l)
                l = f.readline()
            result = self._CloseState(state)
        except IOError:
            if f and f != source:
                f.close()
            self._log.Exception("Read-error for %s" % source)
        return result

    def _InitState(self):
        s = _State();
        s.html = "<div class='izumi'>\n"
        return s

    def _CloseState(self, state):
        state.html += "</div>\n"
        return state.html, state.tags, state.cats, state.images

    def _ProcessLine(self, state, line):
        # placeholder
        state.html += line

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
