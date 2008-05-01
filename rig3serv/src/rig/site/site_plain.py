#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "plain" theme 

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from rig.site.site_default import SiteDefault

#------------------------
class SitePlain(SiteDefault):
    """
    Describes how to generate the content of a site using the "plain" theme.
    
    The "plain" theme inherits from the "default" theme and simply redefines
    some of the HTML templates. The behavior is the same as the default theme
    so the implementation is mostly empty, except for the part that find
    template files: if a file is not found in the plain template, one from the
    default template will be used.
    """

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the default theme's template
        directory. If a file is not found in the plain template directory,
        one will be returned for the default directory -- if this later one
        doesn't exist either, that's a problem with the calling site generator
        and we don't attemp to hide it nor fix it.
        """
        template_file = super(SitePlain, self)._TemplatePath(path, theme="plain")
        if os.path.exists(template_file):
            return template_file
        return super(SitePlain, self)._TemplatePath(path, theme="default")


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
