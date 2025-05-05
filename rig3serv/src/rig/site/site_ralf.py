#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "ralf" theme

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = "ralfoide at gmail com"

import os
from rig.site.site_default import SiteDefault

THEME="ralf"

#------------------------
class SiteRalf(SiteDefault):
    """
    Describes how to generate the content of a site using the "ralf" theme.

    Right now the "ralf" theme is identicaly to the "default" theme
    so the implementation is empty. This is expected to change later.
    """

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the default theme's template
        directory.
        """
        target = super(SiteRalf, self)._TemplatePath(path, theme=THEME)
        if not os.path.exists(target):
            target = super(SiteRalf, self)._TemplatePath(path, theme="default")
        return target

    def _TemplateThemeDirs(self, **keywords):
        """
        Add our custom directory to the theme directories.
        """
        default = super(SiteRalf, self)._TemplateThemeDirs(theme="default")
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
