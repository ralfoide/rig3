#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "plain" theme

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
