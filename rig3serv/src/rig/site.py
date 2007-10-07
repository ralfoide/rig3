#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site definition and actions

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import sys

#------------------------
class Site:
    """
    Describes on site and what we can do with it.
    """
    def __init__(self, public_name, source_dir, dest_dir, theme):
        self._public_name = public_name
        self._source_dir = source_dir
        self._dest_dir = dest_dir
        self._theme = theme
    
    def Process(self):
        """
        Processes the site. Do whatever is needed to get the job done.
        """

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
