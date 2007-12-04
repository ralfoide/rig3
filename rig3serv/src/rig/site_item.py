#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site item

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

#------------------------
class SiteItem(object):
    """
    Represents an item:
    - list of categories (list of string)
    - content: the data of the file
    - date (datetime)
    - rel_filename: filename of the generated file relative to the site's
                    dest_dir.
    """
    def __init__(self, date, rel_filename, content, categories=None):
        self.date = date
        self.content = content
        self.categories = categories or []
        self.rel_filename = rel_filename

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
