#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3 site generation.

This is a "live" test that actually generates data in testdata/live_dest.

The destination directory (testdata/live_dest) is excluded from svn.

Note that the whole point here is that the templates exercised are the
"real" ones from rig3serv/templates. So this kinds of acts as a
"test coverage" for the templates themselves.

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

from tests.rig_test_case import RigTestCase
from rig3 import Rig3
from rig.site.site_default import SiteDefault


_DEST_DIR = "live_dest"  # in testdata dir

#------------------------
class Rig3LiveTest(RigTestCase):

    def setUp(self):
        self._pwd = os.getcwd()
        self._testdata = self.getTestDataPath()
        # all paths are relative to the testdata dir
        os.chdir(self._testdata)
        # cleanup output and make sure it's not there anymore
        self.RemoveDir(_DEST_DIR)
        self.assertFalse(os.path.exists(_DEST_DIR))
        os.mkdir(_DEST_DIR)
        self.assertTrue(os.path.exists(_DEST_DIR))
        self.m = Rig3()

    def tearDown(self):
        os.chdir(self._pwd)
        self.m = None

    def testLive(self):
        t = self._testdata
        rc = os.path.join(t, "z_last_rig3_live.rc")
        args = [ "rig3", "-c", rc ]
        self.m.ParseArgs(args)
        self.m.Run()
        self.m.Close()

        d = os.path.join(t, _DEST_DIR)

        self.assertTrue(os.path.exists(os.path.join(d, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(d, "atom.xml")))
        self.assertTrue(os.path.exists(os.path.join(d, "media", "style.css")))

        f = file(os.path.join(d, "index.html"), "r")
        index_izu = f.read()
        f.close()

        # check accent conversion to html
        self.assertSearch("&ccedil;a, o&ugrave; est le pr&eacute; pr&egrave;s du pr&ecirc;t",
                          index_izu)
        # check tracking inclusion
        self.assertSearch("<i>tracking code here</i>", index_izu)
        # check that riglinks are properly expanded
        self.assertSearch(r'Rig link: <a title="This is a rig link" href="http://rig.base.url/photos1/index.php\?album=2007-10-07_Folder%201&img=T12896_tiny_jpeg.jpg">This is a rig link</a>',
                          index_izu)
        # file items which use the file name as title should loose their extension
        self.assertHtmlSearch('<td class="title">\s*<a name="Izu-File-Item" title="Permalink to \'Izu File Item\'"><a href="post_2007-09-09_Izu-File-Item.html" title="Permalink to \'Izu File Item\'"><span class="date">2007/09/09</span>Izu File Item</a></a></td></tr>',
                               index_izu)
        # sub-directories are parsed for file items too
        self.assertHtmlSearch('<td class="title">\s*<a name="Sub-File-Item" title="Permalink to \'Sub File Item\'"><a href="post_2008-01-02_Sub-File-Item.html" title="Permalink to \'Sub File Item\'"><span class="date">2008/01/02</span>Sub File Item</a></a></td></tr>',
                               index_izu)
        # posts with no tags/categories are accepted
        self.assertHtmlSearch('<td class="title">\s*<a name="No-Tags" title="Permalink to \'No Tags\'"><a href="post_2007-10-02_No-Tags.html" title="Permalink to \'No Tags\'"><span class="date">2007/10/02</span>No Tags</a></a></td></tr>',
                               index_izu)
        # empty posts are accepted
        self.assertHtmlSearch('<td class="title">\s*<a name="Empty-Post" title="Permalink to \'Empty Post\'"><a href="post_2007-10-01_Empty-Post.html" title="Permalink to \'Empty Post\'"><span class="date">2007/10/01</span>Empty Post</a></a></td></tr>',
                               index_izu)



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
