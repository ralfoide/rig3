#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Describes Rig3 information version.

Note: The following SVN keywords are enabled for substitution:
-   Date
-   Revision
-   Author
-   HeadURL
-   Id

To enable substitutions, do something like this:
  $ svn propset svn:keywords "Date Author Revision HeadURL Id" version.py

-----

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

import re

#------------------------
class Version(object):

    SVN_DATE = "$Date$"
    SVN_REVISION = "$Revision$"
    SVN_AUTHOR = "$Author$"
    SNV_HEAD_URL = "$HeadURL$"
    SVN_ID = "$Id$"

    RIG3_VERSION = (0, 4)

    def Version(self):
        """
        Returns the rig3 version as a tuple (major, minor)
        """
        return self.RIG3_VERSION

    def VersionString(self):
        """
        Returns the version number as a string, e.g. "0.1"
        """
        return "%s.%s" % self.RIG3_VERSION

    def SvnRevision(self, revision=SVN_REVISION):
        """
        Returns the Rig3 SVN revision number as an integer.
        If there is no such revision number, returns the string 'Unknown'.

        For the SVN_REVISION to change, it is necessary for this file to be
        edited and checked in. Thus this represents the *last* revision of this
        file, not the one from the whole rig source code.
        TODO: find a way to address this.
        """
        m = re.search("([0-9]+)", revision)
        try:
            return int(m.group(1))
        except ValueError:
            return "Unknown"
        except AttributeError:
            return "Unknown"

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
