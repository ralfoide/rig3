#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3 site generation.
This is a "live" test that actually generates data in testdat/live_dest.
The destination directory is excluded from svn.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig3 import Rig3
from rig.site.site_default import SiteDefault


_DEST_DIR = "live_dest"  # in testdat dir

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
        d = os.path.join(t, _DEST_DIR)
        rc = os.path.join(t, "z_last_rig3_live.rc")
        args = [ "rig3", "-c", rc ]
        self.m.ParseArgs(args)
        self.m.Run()
        self.m.Close()
        
        self.assertTrue(os.path.exists(os.path.join(d, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(d, "media", "style.css")))

        if SiteDefault._TEMPLATE_NEED_ITEM_FILES:
            self.assertTrue(os.path.exists(os.path.join(d, "items", "2007-10-07_Folder-1-index_izu")))
            self.assertTrue(os.path.exists(os.path.join(d, "items", "2006-08-05-20_00_38-Progress-index_html")))

        f = file(os.path.join(d, "index.html"), "r")
        index_izu = f.read()
        f.close()
        self.assertSearch("&ccedil;a, o&ugrave; est le pr&eacute; pr&egrave;s du pr&ecirc;t",
                          index_izu)
        self.assertSearch("<i>tracking code here</i>", index_izu)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
