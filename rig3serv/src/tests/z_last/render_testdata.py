#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Rig3 site generation.

This test does a "live" test using the album source from testdata/album
and the template from testdata/templates.

Contrary to test_rig3_live.py/Rig3LiveTest, this does not exercise the
"real" template, just the testdata/templates one.

The destination directory (testdata/test_dest) is excluded from svn.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig3 import Rig3
from rig.site.site_default import SiteDefault


_DEST_DIR = "test_dest"  # in testdata dir

#------------------------
class RenderTestdata(RigTestCase):

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

    def testRender(self):
        """
        Tests using the testdata/templates/default & magic template
        """
        t = self._testdata
        rc = os.path.join(t, "z_last_render_testdata.rc")
        args = [ "rig3", "-c", rc ]
        self.m.ParseArgs(args)
        self.m.Run()
        self.m.Close()

        d = os.path.join(t, _DEST_DIR, "default")
        self.assertTrue(os.path.exists(os.path.join(d, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(d, "atom.xml")))
        self.assertTrue(os.path.exists(os.path.join(d, "media", "style.css")))

        d = os.path.join(t, _DEST_DIR, "magic")
        self.assertTrue(os.path.exists(os.path.join(d, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(d, "atom.xml")))
        self.assertTrue(os.path.exists(os.path.join(d, "media", "style.css")))
        


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
