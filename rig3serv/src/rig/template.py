#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import sys

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
                return self._Parse(_file.read())
        elif source is not None:
            return self._Parse(source)
        raise TypeError("Template: missing file or source parameters")

    def _ParseFile(self, filename):
        f = None
        try:
            f = file(filename)
            self._Parse(f.read())
        finally:
            if f: f.close()

    def _Parse(self, source):
        pass

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
