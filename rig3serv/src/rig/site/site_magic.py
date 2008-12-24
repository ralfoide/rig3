#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "magic" theme 

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import os
from rig.site.site_default import SiteDefault

THEME="magic"

#------------------------
class SiteMagic(SiteDefault):
    """
    Describes how to generate the content of a site using the "magic" theme.
    
    Right now the "magic" theme is identicaly to the "default" theme
    so the implementation is empty. This is expected to change later.
    """

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the magic theme's template
        directory. If this target file does not exist, use one from the
        default theme.
        """
        target = super(SiteMagic, self)._TemplatePath(path, theme=THEME)
        if not os.path.exists(target):
            target = super(SiteMagic, self)._TemplatePath(path, theme="default")
        return target

    def _TemplateThemeDirs(self, **keywords):
        """
        Add our custom directory to the theme directories.
        """
        default = super(SiteMagic, self)._TemplateThemeDirs(theme="default")
        return [ os.path.join(self._TemplateDir(), THEME) ] + default


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
