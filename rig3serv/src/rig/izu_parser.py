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
        html = ""
        tags = []
        images = []
        cats = []
        try:
            if isinstance(source, str):
                f = file(source, "r", 1)  # 1=line buffered
            else:
                f = source
            state = { "html": html, "tags": tags, "img": images, "cat": cats }
            for l in 
        except IOError:
            if f and f != source:
                f.close()
            self._log.Exception("Read-error for %s" % source)
        return (html, tags, cats, images)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
